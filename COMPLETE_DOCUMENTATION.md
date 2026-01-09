# YOLO Object Detection & Servo Tracking System - Complete Documentation

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Hardware Components](#3-hardware-components)
4. [Software Components](#4-software-components)
5. [Installation Guide](#5-installation-guide)
6. [Usage Instructions](#6-usage-instructions)
7. [Configuration Options](#7-configuration-options)
8. [Technical Details](#8-technical-details)
9. [Troubleshooting](#9-troubleshooting)
10. [Future Enhancements](#10-future-enhancements)

---

## 1. Project Overview

### 1.1 What is this Project?

The **YOLO Object Detection & Servo Tracking System** is a real-time computer vision project that combines artificial intelligence with hardware control to create an automated object tracking camera system. The system uses YOLO (You Only Look Once) object detection algorithms to identify objects in a video feed and automatically moves a pan-tilt camera mechanism to keep the largest detected object centered in the frame.

### 1.2 Key Objectives

- **Real-time Object Detection**: Implement efficient object detection that can run on older hardware
- **Automated Tracking**: Create a system that autonomously follows moving objects
- **Hardware Integration**: Connect computer vision software with physical servo motors via microcontroller
- **CPU Optimization**: Ensure the system runs smoothly on resource-constrained devices

### 1.3 Supported Microcontrollers

The system supports two popular ESP microcontroller families:
- **ESP32**: Dual-core microcontroller with built-in WiFi and Bluetooth
- **ESP8266**: Single-core WiFi-enabled microcontroller (cost-effective alternative)

### 1.4 Supported Detection Models

The project supports multiple detection backends:
1. **YOLOv8 (Ultralytics)**: State-of-the-art object detection with 80+ class support
2. **OpenCV DNN (MobileNet-SSD)**: Lightweight alternative with 20 class support

---

## 2. System Architecture

### 2.1 High-Level Data Flow

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   USB Webcam    │ ──────► │  Python Script   │ ──────► │  ESP32/ESP8266  │
│  (Video Input)  │  USB    │  (YOLO + Logic)  │  Serial │  (Servo Control)│
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │   Display Window │
                         │  (OpenCV GUI)    │
                         └──────────────────┘
```

### 2.2 Component Breakdown

#### Computer Vision Layer (Python)
- Captures frames from USB webcam
- Runs YOLO object detection on each frame
- Identifies the largest detected object
- Calculates object position relative to frame center
- Determines when servo movement is needed
- Sends commands to ESP32 via serial communication

#### Control Logic Layer (Python)
- **Edge-Triggered Tracking**: Only moves servos when object approaches frame edges
- **PID-Style Control**: Proportional control for smooth servo movement
- **Position Smoothing**: Moving average filter to prevent jitter
- **Auto-Return**: Returns to base position when no object detected

#### Hardware Control Layer (ESP32/ESP8266)
- Receives serial commands from Python script
- Controls two SG90 micro servos (pan and tilt)
- Implements smooth servo movement with step control
- Validates and processes incoming commands

### 2.3 Tracking Logic

The system uses an **edge-triggered approach** rather than continuous tracking:

1. **Detection Phase**: YOLO processes each frame and identifies all objects
2. **Selection Phase**: System picks the largest object (largest bounding box area)
3. **Position Calculation**: Computes object center point and bounding box coordinates
4. **Edge Detection**: Checks if object bounding box exceeds trigger zones:
   - **Critical Zone** (20px from edge): Servo MUST move to follow
   - **Warning Zone** (45px from edge): Object approaching edge
5. **Direction Determination**: 
   - Object left of center → Pan moves RIGHT
   - Object right of center → Pan moves LEFT
   - Object above center → Tilt moves DOWN
   - Object below center → Tilt moves UP
6. **Command Sending**: Sends pan/tilt angles to ESP32

---

## 3. Hardware Components

### 3.1 Bill of Materials

| Component | Specification | Purpose | Quantity |
|-----------|---------------|---------|----------|
| Microcontroller | ESP32 or ESP8266 | Servo control & serial communication | 1 |
| Pan Servo | SG90 Micro Servo | Horizontal (left-right) camera movement | 1 |
| Tilt Servo | SG90 Micro Servo | Vertical (up-down) camera movement | 1 |
| Webcam | USB Webcam | Object detection video input | 1 |
| Jumper Wires | Male-to-Female, Male-to-Male | Electrical connections | 10 |
| USB Cable | Micro USB or USB-C | Power & programming for ESP | 1 |
| USB Cable (Webcam) | USB-A to Webcam | Video data connection | 1 |
| Power Supply | 5V 2A (optional) | External power for servos | 1 |

### 3.2 ESP32 Pin Configuration

```
┌─────────────────────────────────────────────────────────┐
│                    ESP32 Dev Module                      │
│                                                         │
│  GND ──────────────────────────────────┬──► Servo GND  │
│  3.3V/5V ──────────────────────────────┼──► Servo VCC  │
│                                         │               │
│  GPIO 2 (D2) ─────────────────────────►│──► Pan Signal │
│  GPIO 13 (D13) ───────────────────────►│──► Tilt Signal│
│                                                         │
│  USB Serial ──────────────────────────►│──► Computer   │
└─────────────────────────────────────────────────────────┘
```

#### Pin Assignment Details:
- **Pan Servo Signal**: GPIO 2
  - Reliable PWM output on most ESP32 boards
  - Labeled as "D2" on many development boards
  
- **Tilt Servo Signal**: GPIO 13
  - Changed from GPIO 4 due to PWM issues
  - GPIO 4 may not support proper PWM on some ESP32 variants

#### Power Considerations:
- **USB Power**: Sufficient for testing with light loads
- **External Power**: Recommended for continuous servo operation
- **Current Draw**: Two SG90 servos can draw up to 500mA peak

### 3.3 ESP8266 Pin Configuration

```
┌─────────────────────────────────────────────────────────┐
│                   NodeMCU ESP8266                        │
│                                                         │
│  GND ──────────────────────────────────┬──► Servo GND  │
│  3.3V/5V ──────────────────────────────┼──► Servo VCC  │
│                                         │               │
│  D2 (GPIO 2) ─────────────────────────►│──► Pan Signal │
│  D4 (GPIO 4) ─────────────────────────►│──► Tilt Signal│
│                                                         │
│  Micro USB ───────────────────────────►│──► Computer   │
└─────────────────────────────────────────────────────────┘
```

### 3.4 Servo Mechanical Setup

#### Pan Servo (Horizontal Movement)
- Mounted on base/stand
- Horn/arm attached to camera mount
- Rotation axis perpendicular to ground
- Range: 5° to 175° (prevents hitting mechanical limits)

#### Tilt Servo (Vertical Movement)
- Mounted on pan servo output
- Camera attached to tilt servo horn
- Rotation axis parallel to ground
- Range: 10° to 170° (prevents hitting mechanical limits)

### 3.5 Camera Mounting Recommendations

```
    ┌─────────┐
    │  Camera │  ← Tilt servo rotates this up/down
    └────┬────┘
         │ Tilt Servo Horn
         ▼
    ┌─────────┐
    │         │  ← Pan servo rotates this left/right
    └────┬────┘
         │ Pan Servo Horn
         ▼
    ┌─────────┐
    │  Base   │
    └─────────┘
```

---

## 4. Software Components

### 4.1 Project File Structure

```
cam/
├── yolo_object_tracker.py              # Main Python tracking script (600+ lines)
├── test_cam.py                         # Original face detection reference
├── requirements.txt                    # Python dependencies list
├── PROJECT_PLAN.md                     # Project planning document
├── TODO.md                             # Task tracking document
├── README.md                           # Quick start guide
│
├── esp_servo_controller/
│   └── esp_servo_controller.ino        # ESP32/ESP8266 Arduino sketch
│
├── models/
│   ├── classes.txt                     # OpenCV DNN class names (20 classes)
│   ├── deploy.prototxt                 # Caffe model definition
│   └── mobilenet_iter_73000.caffemodel # Pre-trained weights
│
└── yolov8n.pt                          # YOLOv8 nano weights (auto-downloaded)
```

### 4.2 Python Script Components

The main Python script (`yolo_object_tracker.py`) is organized into these sections:

#### Configuration Section
```python
# Serial Communication Settings
SERIAL_PORT = '/dev/ttyUSB0'  # ESP32 communication port
BAUD_RATE = 115200            # Communication speed
SERIAL_TIMEOUT = 1            # Timeout in seconds

# Camera Settings
CAMERA_INDEX = 2              # Webcam device index
FRAME_WIDTH = 320             # Frame width (reduced for CPU performance)
FRAME_HEIGHT = 240            # Frame height
CAMERA_FPS = 15               # Frames per second

# Performance Optimization
SKIP_FRAMES = 2               # Process every Nth frame
CONFIDENCE_THRESHOLD = 0.6    # Detection confidence threshold
```

#### Core Functions

1. **Initialization Functions**
   - `init_serial()`: Establishes USB serial connection to ESP32
   - `init_camera()`: Configures webcam with optimized settings
   - `init_yolo()`: Loads YOLOv8 or OpenCV DNN model

2. **Detection Functions**
   - `detect_objects_ultralytics()`: YOLOv8 detection wrapper
   - `detect_objects_opencv()`: OpenCV DNN detection wrapper

3. **Control Functions**
   - `calculate_servo_positions()`: Determines new pan/tilt angles
   - `apply_smoothing_filter()`: Moving average for position smoothing
   - `send_servo_positions()`: Sends commands to ESP32

4. **Visualization Functions**
   - `draw_detections()`: Renders bounding boxes on frame
   - `draw_info()`: Displays status, FPS, and servo positions

5. **Main Loop**
   - `main()`: Orchestrates the complete tracking pipeline

### 4.3 ESP32 Firmware Components

The Arduino sketch (`esp_servo_controller.ino`) contains:

#### Configuration Constants
```cpp
// Pin Definitions
#define PAN_SERVO_PIN 2     // GPIO 2
#define TILT_SERVO_PIN 13   // GPIO 13

// Servo Parameters
#define MIN_PULSE 500       // Minimum PWM pulse width (µs)
#define MAX_PULSE 2500      // Maximum PWM pulse width (µs)
#define SERVO_FREQUENCY 50  // PWM frequency (Hz)
```

#### Global Variables
```cpp
Servo panServo;      // Pan servo object
Servo tiltServo;     // Tilt servo object
int panAngle = 90;   // Current pan position
int tiltAngle = 90;  // Current tilt position
int targetPan = 90;  // Target pan position
int targetTilt = 90; // Target tilt position

const int STEP_SIZE = 3;       // Movement per update (degrees)
const int UPDATE_DELAY = 25;   // Time between updates (ms)
```

#### Key Functions
- `setup()`: Initializes serial, servos, and default positions
- `loop()`: Main program loop for command processing
- `parseTrackingCommand()`: Parses "PAN,TILT" format commands
- `updateServos()`: Smoothly moves servos toward targets

#### Supported Commands
| Command | Format | Description |
|---------|--------|-------------|
| Test Pan | `P,90` | Move pan servo to 90° |
| Test Tilt | `T,90` | Move tilt servo to 90° |
| Both Servos | `B,90,90` | Move both servos simultaneously |
| Sweep Test | `S` | Run sweep animation |
| Tracking | `90,90` | Normal tracking command |

### 4.4 Model Specifications

#### YOLOv8 Nano (Primary)
- **File**: `yolov8n.pt`
- **Classes**: 80 COCO dataset classes
- **Input Size**: 320×320 pixels
- **Inference Speed**: ~3-5 FPS on old CPUs
- **Accuracy**: Good balance of speed and precision

#### OpenCV DNN MobileNet-SSD (Fallback)
- **Files**: `deploy.prototxt` + `mobilenet_iter_73000.caffemodel`
- **Classes**: 20 classes (aeroplane, bicycle, bird, boat, bottle, bus, car, cat, chair, cow, diningtable, dog, horse, motorbike, person, pottedplant, sheep, sofa, train, tvmonitor)
- **Input Size**: 300×300 pixels
- **Inference Speed**: ~5-8 FPS on old CPUs
- **Accuracy**: Lower but faster than YOLOv8

---

## 5. Installation Guide

### 5.1 System Requirements

#### Minimum Hardware
- **Processor**: Intel Atom or similar (2015-era laptop)
- **RAM**: 2 GB available
- **USB Ports**: 2 available (webcam + ESP32)
- **Webcam**: Any USB webcam

#### Supported Operating Systems
- Linux (Ubuntu/Debian recommended)
- macOS
- Windows 10/11

### 5.2 Python Environment Setup

#### Step 1: Create Virtual Environment
```bash
# Navigate to project directory
cd /home/meet-patel/Documents/cam

# Create virtual environment
python -m venv cam_env

# Activate virtual environment
# Linux/Mac:
source cam_env/bin/activate

# Windows:
cam_env\Scripts\activate
```

#### Step 2: Install Dependencies
```bash
# Core dependencies
pip install opencv-python numpy pyserial

# YOLOv8 (Ultralytics) - recommended
pip install ultralytics

# Optional: ONNX Runtime for faster inference
pip install onnxruntime
```

#### Step 3: Verify Installation
```bash
# Test Python imports
python -c "import cv2; import serial; from ultralytics import YOLO"
print("All dependencies installed successfully!")
```

### 5.3 ESP32/ESP8266 Setup

#### Step 1: Install Arduino IDE
1. Download from https://www.arduino.cc/en/software
2. Install according to your operating system

#### Step 2: Install Board Support
**For ESP32:**
1. Open Arduino IDE
2. Go to File → Preferences
3. Add ESP32 board URL:
   ```
   https://espressif.github.io/arduino-esp32/package_esp32_index.json
   ```
4. Go to Tools → Board → Boards Manager
5. Search "ESP32" and install

**For ESP8266:**
1. Go to File → Preferences
2. Add ESP8266 board URL:
   ```
   https://arduino.esp8266.com/stable/package_esp8266com_index.json
   ```
3. Search "ESP8266" in Boards Manager and install

#### Step 3: Install Servo Library
- The Servo library is usually bundled with ESP32/ESP8266 board support
- If needed: Sketch → Include Library → Manage Libraries → Search "ESP32Servo" → Install

#### Step 4: Upload Firmware
1. Connect ESP32 to computer via USB
2. Open `esp_servo_controller/esp_servo_controller.ino` in Arduino IDE
3. Select your board: Tools → Board → ESP32 Dev Module
4. Select correct port: Tools → Port → /dev/ttyUSB0 (Linux) or COM3 (Windows)
5. Click Upload button (→ arrow icon)
6. Wait for "Done uploading" message

### 5.4 Serial Port Permissions (Linux)

If you encounter permission issues:
```bash
# Add user to dialout group
sudo usermod -aG dialout $USER

# Log out and log back in for changes to take effect

# Or temporarily use sudo
sudo python yolo_object_tracker.py
```

### 5.5 Model Download

The YOLOv8 nano model (`yolov8n.pt`) is automatically downloaded on first run. For manual download:
```bash
# Download YOLOv8n
wget https://github.com/ultralytics/assets/releases/download/v8.0.0/yolov8n.pt
```

---

## 6. Usage Instructions

### 6.1 Running the System

#### Step 1: Activate Python Environment
```bash
# Linux/Mac
source cam_env/bin/activate

# Windows
cam_env\Scripts\activate
```

#### Step 2: Run the Tracker
```bash
python yolo_object_tracker.py
```

#### Step 3: Expected Output
```
==================================================
YOLO Object Detection & Servo Tracking System
CPU-Optimized for Old Laptops
==================================================
✓ Connected to ESP on /dev/ttyUSB0
✓ Camera initialized (Index: 2, 320x240 @ 15fps)
✓ YOLOv8 model loaded (CPU mode)

Starting tracking... Press 'q' to quit
--------------------------------------------------
```

### 6.2 On-Screen Display

The application displays a window with tracking information, detected objects with bounding boxes, and status indicators. The display shows:
- Current tracking status (Tracking, No Object, Error)
- Pan and tilt angles
- Frames per second (FPS)
- Bounding boxes with class names and confidence scores
- Critical and warning zone markers
- Instructions for quitting

### 6.3 Visual Indicators

#### Detection Display
- **Green bounding box**: Detected object
- **Label**: Object class + confidence percentage
- **Multiple objects**: All detected objects shown

#### Tracking Zones
- **Yellow rectangle**: Critical zone (20px from edges) - triggers servo movement
- **White rectangle**: Warning zone (45px from edges) - object approaching edge
- **Red cross**: Frame center point

#### Status Messages
| Status | Meaning |
|--------|---------|
| Starting | System initializing |
| Tracking | Object detected, following it |
| No Object - Returning to Base | No objects found, returning home |
| Error | Something went wrong |

### 6.4 Keyboard Controls

| Key | Action |
|-----|--------|
| `q` | Quit the application |
| `ESC` | Alternative quit method |

### 6.5 Serial Communication Protocol

#### Format
```
PAN,TILT\n
Example: 90,45\n
```

#### Value Ranges
- **Pan**: 0° to 180° (recommended: 5° to 175°)
- **Tilt**: 0° to 180° (recommended: 10° to 170°)

#### ESP32 Response
```
Target -> Pan: 90°, Tilt: 45°
```

---

## 7. Configuration Options

### 7.1 Serial Communication Settings

```python
# Serial Communication
SERIAL_PORT = '/dev/ttyUSB0'  # Change to match your ESP32 port
BAUD_RATE = 115200            # Communication speed (standard: 115200)
SERIAL_TIMEOUT = 1            # Serial read timeout (seconds)
```

**Finding the correct port:**
```bash
# Linux
ls /dev/ttyUSB*  # ESP32 devices
ls /dev/ttyACM*  # Some ESP devices

# Windows
# Check Device Manager → Ports (COM & LUSB)
# Look for "USB Serial Port (COMX)"
```

### 7.2 Camera Settings

```python
# Camera Settings
CAMERA_INDEX = 2              # 0 = built-in, 1 = first USB, 2 = second USB
FRAME_WIDTH = 320             # Reduce to 160 for faster processing
FRAME_HEIGHT = 240            # Reduce to 120 for faster processing
CAMERA_FPS = 15               # Reduce to 10 for slower computers
```

**Finding the correct camera index:**
```python
import cv2

# Test different camera indices
for i in range(5):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"Camera {i} is available")
        cap.release()
    else:
        print(f"Camera {i} not available")
```

### 7.3 Performance Optimization

```python
# Performance Settings
SKIP_FRAMES = 2               # 1 = process all, 2 = every other, 3 = 1 in 3
CONFIDENCE_THRESHOLD = 0.6    # Lower = more detections, slower
```

**Recommended settings by hardware:**

| Hardware | FRAME_SIZE | FPS | SKIP_FRAMES | CONFIDENCE |
|----------|------------|-----|-------------|------------|
| Old Laptop (Atom/Celeron) | 320×240 | 10 | 3 | 0.7 |
| Old Laptop (i3/i5) | 320×240 | 15 | 2 | 0.6 |
| Modern Laptop (i5/i7) | 640×480 | 30 | 1 | 0.5 |
| Desktop (any) | 640×480 | 30 | 1 | 0.5 |

### 7.4 Servo Settings

```python
# Base Positions (where camera points when idle)
BASE_PAN = 90                 # Horizontal center
BASE_TILT = 90                # Vertical center

# Physical Limits
PAN_MIN, PAN_MAX = 5, 175     # Prevent hitting mechanical limits
TILT_MIN, TILT_MAX = 10, 170  # Prevent hitting mechanical limits
```

### 7.5 Tracking Control

```python
# Proportional Control (PID-style)
KP_PAN = 0.25                 # Pan proportional gain (higher = faster response)
KP_TILT = 0.25                # Tilt proportional gain

# Movement Limits
MAX_STEP = 5                  # Maximum degrees per frame
EDGE_MARGIN = 20              # Critical zone size (pixels)
WARNING_MARGIN = 45           # Warning zone size (pixels)
```

**Adjusting tracking sensitivity:**

| Behavior | EDGE_MARGIN | KP_PAN/KP_TILT | MAX_STEP |
|----------|-------------|----------------|----------|
| Too slow to track | Decrease | Increase | Increase |
| Too jittery | Increase | Decrease | Decrease |
| Missing fast objects | Decrease | Increase | Increase |
| Servo oscillating | Increase | Decrease | Decrease |

### 7.6 Smoothing Settings

```python
# Position Smoothing (Moving Average Filter)
SMOOTHING_WINDOW = 5          # Number of frames to average
DEAD_ZONE = 0                 # No movement threshold (pixels)
```

### 7.7 Display Settings

```python
DISPLAY_FPS = True            # Show FPS counter
DEBUG_MODE = True             # Print debug info to console
```

---

## 8. Technical Details

### 8.1 Detection Algorithms

#### YOLOv8 Architecture
YOLOv8 (You Only Look Once, version 8) is a family of object detection models developed by Ultralytics. Key characteristics:

- **Single-pass detection**: Processes entire image in one forward pass
- **CSPDarknet backbone**: Feature extraction network
- **PANet neck**: Feature pyramid network for multi-scale detection
- **YOLOv8 Head**: Detection head for bounding box prediction

**Why YOLOv8 Nano?**
- Smallest and fastest model in the family
- Designed for edge devices and resource-constrained environments
- Good accuracy-to-speed ratio
- Native Python support via Ultralytics library

#### OpenCV DNN MobileNet-SSD
Fallback option using Caffe-based MobileNet with SSD (Single Shot Detector):

- **MobileNet backbone**: Lightweight depthwise separable convolutions
- **SSD**: Multi-scale object detection
- **Caffe framework**: Pre-trained model format
- **CPU-optimized**: OpenCV's DNN module uses AVX/AVX2 optimizations

### 8.2 Coordinate Systems

#### Frame Coordinates
```
(0,0) ──────────────► X (width)
   │
   │
   │
   ▼ Y (height)
   
Center = (FRAME_WIDTH // 2, FRAME_HEIGHT // 2)
```

#### Bounding Box Format
```
[x1, y1, x2, y2]
- x1, y1: Top-left corner
- x2, y2: Bottom-right corner
- Width = x2 - x1
- Height = y2 - y1
- Area = Width × Height
```

#### Servo Angle System
```
        0° (left)
         │
         │
    Pan  │
   Servo │
         │
        90° (center) ◄── BASE_PAN
         │
         │
         │
       180° (right)

       0° (down)
         │
         │
        90° (center) ◄── BASE_TILT
         │
         │
       180° (up)
```

### 8.3 Control Algorithm

#### Edge-Triggered Logic
The system uses a trigger-based approach rather than continuous tracking:

```
IF (object_left < EDGE_MARGIN) OR (object_right > FRAME_WIDTH - EDGE_MARGIN):
    # Object is near horizontal edges
    IF object_left < EDGE_MARGIN:
        # Object on LEFT side → move pan RIGHT
        direction = +1
        error = EDGE_MARGIN - object_left
    ELSE:
        # Object on RIGHT side → move pan LEFT
        direction = -1
        error = object_right - (FRAME_WIDTH - EDGE_MARGIN)
    
    pan_step = min(KP_PAN × error, MAX_STEP)
    new_pan = current_pan + (direction × pan_step)
```

#### Smoothing Algorithm
```python
def apply_smoothing_filter(pan_history, tilt_history):
    # Moving average filter
    smoothed_pan = sum(pan_history) / len(pan_history)
    smoothed_tilt = sum(tilt_history) / len(tilt_history)
    
    return int(round(smoothed_pan)), int(round(smoothed_tilt))
```

### 8.4 Serial Protocol Details

#### Data Format
- **Baud Rate**: 115200 bits/second
- **Data Bits**: 8
- **Parity**: None
- **Stop Bits**: 1
- **Line Ending**: `\n` (newline)

#### Command Format
```
┌────────────────────────────────────────────┐
│ Byte 0-2    │ Byte 3     │ Byte 4...N     │
├─────────────┼────────────┼────────────────┤
│ PAN (3 dig) │ ',' comma  │ TILT + newline │
└────────────────────────────────────────────┘

Example: "90,45\n"
         "123,67\n"
         " 5,  5\n"
```

#### ESP32 Command Parsing
```cpp
void parseTrackingCommand(String cmd) {
    int commaIndex = cmd.indexOf(',');
    if (commaIndex == -1) return;  // Invalid format
    
    String panStr = cmd.substring(0, commaIndex);
    String tiltStr = cmd.substring(commaIndex + 1);
    
    int panVal = panStr.toInt();
    int tiltVal = tiltStr.toInt();
    
    // Validate ranges
    if (panVal >= 0 && panVal <= 180 && 
        tiltVal >= 0 && tiltVal <= 180) {
        targetPan = panVal;
        targetTilt = tiltVal;
    }
}
```

### 8.5 ESP32 Servo Control

#### PWM Configuration
```cpp
// ESP32Servo library handles PWM automatically
panServo.attach(PAN_SERVO_PIN, MIN_PULSE, MAX_PULSE);

// PWM parameters:
// - Frequency: 50 Hz (20ms period)
// - Pulse width: 500µs to 2500µs
// - Angle mapping: 0° → 500µs, 180° → 2500µs
```

#### Smooth Movement
```cpp
void updateServos() {
    // Step-based movement for smoothness
    if (panAngle < targetPan) {
        panAngle = min(panAngle + STEP_SIZE, targetPan);
        panServo.write(panAngle);
    } else if (panAngle > targetPan) {
        panAngle = max(panAngle - STEP_SIZE, targetPan);
        panServo.write(panAngle);
    }
    // Same for tilt...
    delay(UPDATE_DELAY);
}
```

---

## 9. Troubleshooting

### 9.1 Camera Issues

#### Problem: "Cannot open camera"
```
✗ Cannot open camera 2
```

**Solutions:**
1. Check camera index (try 0, 1, 2)
2. Verify USB connection
3. Test with another application
4. Check camera permissions (Linux):
   ```bash
   sudo chmod 666 /dev/video0
   ```

#### Problem: Green/purple tinted video
**Cause:** Incorrect pixel format

**Solution:** Add this after camera initialization:
```python
cap.set(cv2.CAP_PROP_FORMAT, -1)  # Auto-detect format
```

#### Problem: Low frame rate
**Solutions:**
1. Reduce `FRAME_WIDTH` and `FRAME_HEIGHT`
2. Increase `SKIP_FRAMES`
3. Lower `CAMERA_FPS`
4. Close other applications
5. Disable DEBUG_MODE

### 9.2 Serial Connection Issues

#### Problem: "Serial connection failed"
```
✗ Serial connection failed: [Errno 13] Permission denied
```

**Solutions:**
1. **Linux permissions:**
   ```bash
   sudo usermod -aG dialout $USER
   # Log out and back in
   ```

2. **Wrong port:** Check correct port:
   ```bash
   ls -l /dev/ttyUSB*
   ls -l /dev/ttyACM*
   ```

3. **Port in use:** Close other programs using the port

4. **Wrong baud rate:** Ensure both Python and ESP32 use 115200

#### Problem: "Serial connection failed: [Errno 2]"
**Cause:** Wrong port path

**Solution:** Update SERIAL_PORT in yolo_object_tracker.py

### 9.3 ESP32/Servo Issues

#### Problem: Servo not moving
**Checklist:**
1. [ ] Servo VCC connected to 5V (not 3.3V for SG90)
2. [ ] Servo GND connected to ESP32 GND
3. [ ] Signal wire connected to correct GPIO
4. [ ] External power supply if servos are stiff

#### Problem: Servo jittering
**Solutions:**
1. Increase SMOOTHING_WINDOW
2. Add DEAD_ZONE (e.g., DEAD_ZONE = 10)
3. Reduce MAX_STEP
4. Check power supply stability

#### Problem: Tilt servo not working (GPIO 4)
**Cause:** Some ESP32 boards have PWM issues on GPIO 4

**Solution:**
1. Change TILT_SERVO_PIN from 4 to 13 in esp_servo_controller.ino
2. Re-wire tilt servo to GPIO 13
3. Re-upload firmware

#### Problem: Servo hitting limits
**Solution:** Adjust servo limits:
```python
PAN_MIN, PAN_MAX = 5, 175  # Reduce range
TILT_MIN, TILT_MAX = 10, 170
```

### 9.4 Object Detection Issues

#### Problem: No objects detected
**Solutions:**
1. Lower confidence threshold:
   ```python
   CONFIDENCE_THRESHOLD = 0.3
   ```

2. Check lighting conditions
3. Ensure object is fully visible
4. Verify YOLOv8 model loaded correctly

#### Problem: Wrong objects detected
**Solutions:**
1. Increase CONFIDENCE_THRESHOLD
2. Filter by specific class:
   ```python
   TARGET_CLASS = "person"  # Track only people
   ```

#### Problem: Detection too slow
**Solutions:**
1. Use smaller YOLOv8 model: yolov8n.pt (already smallest)
2. Reduce input size: imgsz=160
3. Skip more frames: SKIP_FRAMES=3
4. Use OpenCV DNN fallback

### 9.5 Performance Issues

#### Low FPS on old laptop
**Optimized settings:**
```python
FRAME_WIDTH = 320
FRAME_HEIGHT = 240
CAMERA_FPS = 10
SKIP_FRAMES = 3
CONFIDENCE_THRESHOLD = 0.7
```

#### Memory errors
**Solutions:**
1. Reduce FRAME_WIDTH/HEIGHT
2. Clear detection history more frequently
3. Restart the application

---

## 10. Future Enhancements

### 10.1 Feature Ideas

#### High Priority
- [ ] **Multi-object tracking**: Track specific class (e.g., only "person")
- [ ] **Object persistence**: Remember object across frames
- [ ] **Web interface**: Monitor and control via browser

#### Medium Priority
- [ ] **Motion prediction**: Anticipate object movement
- [ ] **Smooth interpolation**: Jerk-free servo movements
- [ ] **Logging system**: Record tracking data
- [ ] **Configuration UI**: On-screen settings menu

#### Low Priority
- [ ] **Voice control**: "Track person", "Stop"
- [ ] **Gesture control**: Hand gestures for commands
- [ ] **Object counting**: Count tracked objects
- [ ] **Zone-based tracking**: Only track objects in specific areas

### 10.2 Performance Improvements

- [ ] **Multi-threading**: Separate detection and display threads
- [ ] **GPU acceleration**: Use CUDA for faster inference
- [ ] **Model quantization**: Convert model to INT8
- [ ] **ONNX Runtime**: Faster CPU inference

### 10.3 Hardware Expansions

- [ ] **Pan-tilt kit**: Use official camera mount with bearings
- [ ] **Battery power**: Make system portable
- [ ] **WiFi streaming**: Stream video over network
- [ ] **OLED display**: Show status without computer

### 10.4 Integration Ideas

- [ ] **Home Assistant**: Integrate with smart home
- [ ] **Security system**: Alert on person detection
- [ ] **Video recording**: Record tracked footage
- [ ] **Time-lapse**: Automated movement capture

---

## Appendix A: COCO Dataset Classes (80 classes)

person, bicycle, car, motorcycle, airplane, bus, train, truck, boat, traffic light, fire hydrant, stop sign, parking meter, bench, bird, cat, dog, horse, sheep, cow, elephant, bear, zebra, giraffe, backpack, umbrella, handbag, tie, suitcase, frisbee, skis, snowboard, sports ball, kite, baseball bat, baseball glove, skateboard, surfboard, tennis racket, bottle, wine glass, cup, fork, knife, spoon, bowl, banana, apple, sandwich, orange, broccoli, carrot, hot dog, pizza, donut, cake, chair, couch, potted plant, bed, dining table, toilet, TV, laptop, mouse, remote, keyboard, cell phone, microwave, oven, toaster, sink, refrigerator, book, clock, vase, scissors, teddy bear, hair drier, toothbrush

## Appendix B: OpenCV DNN Classes (20 classes)

background, aeroplane, bicycle, bird, boat, bottle, bus, car, cat, chair, cow, diningtable, dog, horse, motorbike, person, pottedplant, sheep, sofa, train, tvmonitor

---

## Document Information

- **Project**: YOLO Object Detection & Servo Tracking System
- **Version**: 1.0
- **Last Updated**: 2024
- **Author**: System Documentation
- **Purpose**: Complete project documentation from scratch

This document provides comprehensive information about the entire YOLO Object Detection & Servo Tracking System, covering all aspects from hardware setup to software configuration, troubleshooting, and future enhancements.

