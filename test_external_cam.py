#!/usr/bin/env python3
"""
Test external camera (index 2) functionality
"""

import cv2
import time

print("Testing external camera (index 2)...")
print("-" * 40)

# Try different backends for the external camera
backends = [
    (cv2.CAP_V4L2, "V4L2"),
    (cv2.CAP_GSTREAMER, "GStreamer"),
    (cv2.CAP_ANY, "Auto")
]

camera_works = False

for backend, backend_name in backends:
    print(f"Trying {backend_name} backend...", end=" ")
    try:
        cap = cv2.VideoCapture(2, backend)
        
        if cap.isOpened():
            # Set lower resolution for testing
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
            
            # Try to read a frame
            ret, frame = cap.read()
            time.sleep(0.5)  # Give camera time to stabilize
            
            if ret and frame is not None:
                print(f"✓ SUCCESS!")
                print(f"   Resolution: {frame.shape[1]}x{frame.shape[0]}")
                print(f"   Showing test frame for 3 seconds...")
                
                # Show preview window for 3 seconds
                cv2.imshow("External Camera Test (Index 2)", frame)
                cv2.waitKey(3000)
                cv2.destroyAllWindows()
                
                cap.release()
                camera_works = True
                break
            else:
                print(f"✗ Opened but can't read frame")
                cap.release()
        else:
            print(f"✗ Failed to open")
    except Exception as e:
        print(f"✗ Error: {e}")
        try:
            cap.release()
        except:
            pass

print("-" * 40)

if camera_works:
    print("✓ External camera (index 2) is working correctly!")
    print("\nIf it doesn't work in yolo_object_tracker.py, try:")
    print("1. Closing other applications that might be using the camera")
    print("2. Using a different USB port (preferably USB 2.0 for external webcams)")
    print("3. Reducing resolution in the settings")
else:
    print("✗ External camera (index 2) is NOT working!")
    print("\nTroubleshooting steps:")
    print("1. Check USB connection - try a different USB port")
    print("2. Check if camera is being used by another process: lsof /dev/video*")
    print("3. Check camera power - some USB ports don't provide enough power")
    print("4. Try the camera in another application (cheese, guvcview, etc.)")
    print("5. Check dmesg for USB device messages: dmesg | tail")

