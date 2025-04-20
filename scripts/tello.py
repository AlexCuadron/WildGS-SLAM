#!/usr/bin/env python3
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
 
from djitellopy import Tello
#import numpy as np
import time
 
# Initialize GStreamer
Gst.init(None)
 
# Frame counter
frame_idx = 0
 
def on_new_sample(sink, data):
    """Callback when appsink has a new sample."""
    global frame_idx
    sample = sink.emit('pull-sample')
    buf = sample.get_buffer()
 
    # Map the buffer to read raw bytes (this is the PNG data)
    success, mapinfo = buf.map(Gst.MapFlags.READ)
    if not success:
        return Gst.FlowReturn.ERROR
 
    # Write out the PNG
    filename = f"frame_{frame_idx:04d}.png"
    #with open(filename, "wb") as f:
    #    f.write(mapinfo.data)
    print(f"Saved {filename}")
    frame_idx += 1
 
    buf.unmap(mapinfo)
    return Gst.FlowReturn.OK
 
def main():
    
    pipeline = Gst.parse_launch(
        'udpsrc port=11111 ! '
        'queue ! '                                  # buffer a few packets
        'capsfilter caps="video/x-h264, ' 
                    'stream-format=(string)byte-stream" ! '
        'decodebin name=dec ! '                     # auto‑detect parser + decoder
        'queue ! videoconvert ! '
        'queue ! pngenc ! '
        'queue max-size-buffers=1 leaky=downstream ! '
        'appsink name=pngsink emit-signals=true max-buffers=1 drop=true'
    )


 
    # Grab the appsink and attach our callback
    appsink = pipeline.get_by_name("pngsink")
    appsink.connect("new-sample", on_new_sample, None)
 
    # Start playback
    pipeline.set_state(Gst.State.PLAYING)
    print("Running... press Ctrl+C to stop.")
 
    # Run the GLib main loop to process callbacks
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        pass
    finally:
        pipeline.set_state(Gst.State.NULL)
 
if __name__ == "__main__":
    #tello = Tello()
    #tello.connect()
    #tello.streamoff()
    #tello.streamon()
    
    main()
 
