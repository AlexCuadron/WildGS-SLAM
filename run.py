import numpy as np
import torch
import argparse
import os
import cv2
import threading
import multiprocessing as mp
from src.utils.datasets import QueueDataset
from queue import Queue
import time

from src import config
from src.slam import SLAM
from src.utils.datasets import get_dataset
from time import gmtime, strftime
from colorama import Fore,Style

import random
def setup_seed(seed):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    random.seed(seed)
    torch.backends.cudnn.deterministic = True

def image_provider(image_queue, image_dir, max_images=None):
    """
    Continuously loads images from a directory and puts them in the queue.
    
    Args:
        image_queue: Queue to place images in
        image_dir: Directory containing image files (PNG format)
        max_images: Maximum number of images to load (None for all)
    """
    image_files = sorted([f for f in os.listdir(image_dir) if f.endswith('.png')])
    
    if max_images is not None:
        image_files = image_files[:max_images]
    
    print(f"Found {len(image_files)} images in {image_dir}")
    
    # Wait for user input for frames per second
    fps = None
    while fps is None:
        try:
            fps_input = 2 #input("Enter frames per second (FPS) to start loading images: ")
            fps = float(fps_input)
            if fps <= 0:
                print("FPS must be a positive number")
                fps = None
        except ValueError:
            print("Please enter a valid number")
    
    print(f"Starting to load images at {fps} frames per second")
    frame_delay = 1.0 / fps  # Calculate delay between frames in seconds
    
    for img_file in image_files:
        img_path = os.path.join(image_dir, img_file)
        img = cv2.imread(img_path)
        if img is not None:
            #print(f"Loaded image! :D")
            image_queue.put(img)
            time.sleep(frame_delay)  # Delay based on user-specified FPS
        else:
            print(f"Failed to load image: {img_path}")
    
    print("All images have been loaded into the queue")
    
    # Keep the queue filled with the last image to prevent tracker from exiting
    while True:
        if image_queue.qsize() < 2:
            # Add the last image again to keep things running
            image_queue.put(img)
        time.sleep(1.0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=str, help='Path to config file.')
    parser.add_argument('--use_queue', action='store_true', help='Use queue-based image processing instead of file-based')
    parser.add_argument('--image_dir', type=str, help='Directory containing images for queue-based processing (overrides config file)')
    parser.add_argument('--max_images', type=int, default=None, help='Maximum number of images to process in queue mode')
    args = parser.parse_args()

    torch.multiprocessing.set_start_method('spawn')

    cfg = config.load_config(args.config)
    setup_seed(cfg['setup_seed'])
    if cfg['fast_mode']:
        # Force the final refine iterations to be 3000 if in fast mode
        cfg['mapping']['final_refine_iters'] = 300

    output_dir = cfg['data']['output']
    output_dir = output_dir+f"/{cfg['scene']}"

    start_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    start_info = "-"*30+Fore.LIGHTRED_EX+\
                 f"\nStart WildGS-SLAM at {start_time},\n"+Style.RESET_ALL+ \
                 f"   scene: {cfg['dataset']}-{cfg['scene']},\n" \
                 f"   output: {output_dir}\n"+ \
                 "-"*30
    print(start_info)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    config.save_config(cfg, f'{output_dir}/cfg.yaml')

    # Handle queue-based processing if requested
    if args.use_queue:
        # Set dataset type to queue
        cfg['dataset'] = 'queue'
        
        # Get image_dir from command line or from config
        image_dir = args.image_dir
        if image_dir is None:
            # Try to get from config file
            if 'input_folder' in cfg['data']:
                image_dir = cfg['data']['input_folder']
                # Handle path placeholder if present
                if "ROOT_FOLDER_PLACEHOLDER" in image_dir:
                    image_dir = image_dir.replace("ROOT_FOLDER_PLACEHOLDER", cfg['data']['root_folder'])
            
            if image_dir is None or not os.path.exists(image_dir):
                parser.error("No valid image directory provided. Either use --image_dir or set 'input_folder' in config.")
        
        print(f"Using image directory: {image_dir}")
        
        # Create image queue
        image_queue = mp.Queue()
        
        # Start image provider thread
        image_dir = cfg['data']['root_folder']+'/parking/rgb'
        # image_provider(image_queue, image_dir, args.max_images)
        provider_process = mp.Process(
            target=image_provider,
            args=(image_queue, image_dir, args.max_images),
            daemon=True
        )
        provider_process.start()
        
        dataset = QueueDataset(cfg, device='cuda:0', image_queue=image_queue)
        
        # Initialize SLAM with the queue
        slam = SLAM(cfg, dataset, image_queue=image_queue)
    else:
        # Standard file-based processing
        dataset = get_dataset(cfg)
        slam = SLAM(cfg, dataset)

    # Run SLAM
    slam.run()

    end_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    print("-"*30+Fore.LIGHTRED_EX+f"\nWildGS-SLAM finishes!\n"+Style.RESET_ALL+f"{end_time}\n"+"-"*30)

