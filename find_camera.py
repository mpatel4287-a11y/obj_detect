#!/usr/bin/env python3
"""
Find available camera indices
Run this script to see which camera indices work on your system
"""

import cv2

print("Checking available camera indices...")
print("-" * 40)

for i in range(10):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"✓ Camera {i}: WORKING (resolution: {frame.shape[1]}x{frame.shape[0]})")
        else:
            print(f"✓ Camera {i}: Opened but can't read frame")
        cap.release()
    else:
        print(f"✗ Camera {i}: Not available")

print("-" * 40)
print("Try using the working camera index in yolo_object_tracker.py")
print("CAMERA_INDEX = <working_index>")

