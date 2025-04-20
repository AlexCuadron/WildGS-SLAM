# Extract Frames for WildGS-SLAM

This script helps you extract frames from an MP4 video in a format compatible with the Wild_SLAM_iPhone dataset.

## Prerequisites

- Python 3.6 or higher
- OpenCV (`pip install opencv-python`)
- ffmpeg (system installation)

## Installation

To install ffmpeg:

- On Ubuntu/Debian: `sudo apt-get install ffmpeg`
- On macOS with Homebrew: `brew install ffmpeg`
- On Windows: [Download from ffmpeg.org](https://ffmpeg.org/download.html)

## Usage

```bash
python extract_frames.py <video_path> --scene <scene_name> [options]
```

### Arguments

- `video_path`: Path to the MP4 video file (required)
- `--scene`: Name of the scene (required)
- `--output`: Output directory (default: "./datasets/Wild_SLAM_iPhone")
- `--width`: Output image width (default: 1920)
- `--height`: Output image height (default: 1440)
- `--start-frame`: Starting frame number (default: 0)

### Example

```bash
# Basic usage
python extract_frames.py my_video.mp4 --scene my_scene

# Custom output location and resolution
python extract_frames.py my_video.mp4 --scene my_scene --output ./my_dataset --width 1280 --height 720
```

## Output

The script will create:

1. A directory structure like:
   ```
   <output_dir>/
   └── <scene_name>/
       ├── rgb/
       │   ├── frame_00000.png
       │   ├── frame_00001.png
       │   └── ...
       ├── depth/  # Empty directory, for compatibility
       └── calibration.json
   ```

2. A suggested YAML configuration for WildGS-SLAM that you can save to your configs directory.

## Note

The script estimates camera intrinsics based on the output resolution. For more accurate results, you may want to replace these values with the actual intrinsic parameters of your iPhone model if available.