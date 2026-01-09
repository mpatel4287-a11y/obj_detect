# 🎯 YOLO Object Detection & Servo Tracking System

A real-time object detection and tracking system using YOLO, OpenCV, and ESP32/ESP8266 servo control. The camera automatically follows detected objects using a pan-tilt servo mechanism.

![System Overview](https://via.placeholder.com/800x400?text=YOLO+Object+Tracker+System)

## 🌟 Features

- **Real-time Object Detection** using YOLOv8 (Ultralytics) or OpenCV DNN
- **Bounding Box Display** with object name and accuracy percentage
- **Auto-tracking** of the largest detected object
- **Smooth Servo Movement** with PID-style control
- **ESP32/ESP8266 Integration** via serial communication
- **Multi-class Support** (80 COCO classes with YOLOv8, 20 classes with basic model)

## 📁 Project Structure

```
cam/
├── yolo_object_tracker.py     # Main Python tracking script
├── esp_servo_controller/      # Arduino IDE project folder
│   └── esp_servo_controller.ino
├── test_cam.py                # Original face detection (reference)
├── models/                    # Model files
│   ├── classes.txt           # COCO class names
│   ├── deploy.prototxt       # Caffe deployment config
│   └── mobilenet_iter_73000.caffemodel
├── yolov8n.pt                # YOLOv8 nano weights (auto-downloaded)
└── README.md                 # This file
```

## 🔧 Hardware Requirements

| Component | Purpose | Quantity |
|-----------|---------|----------|
| ESP32 or ESP8266 | Servo control microcontroller | 1 |
| SG90 Micro Servo (×2) | Pan (horizontal) & Tilt (vertical) movement | 2 |
| USB Webcam | Object detection camera | 1 |
| Jumper Wires | Connections | ~10 |
| USB Cable | Power & data to ESP | 1 |

### 📐 Pin Connections

```
ESP32/ESP8266          Servo Motors
─────────────────────────────────────
GPIO 2  (or D2)   →    Pan Servo Signal (Orange/Yellow)
GPIO 13 (or D13)  →    Tilt Servo Signal (Orange/Yellow)  [Changed from GPIO 4]
3.3V or 5V        →    Servo VCC (Red)
GND               →    Servo GND (Brown)
```

### 🔌 Camera Connection
- **USB Webcam** → Connect to laptop/computer USB port
- **Note**: Camera index may need to be changed in code (0, 1, or 2)

## 🚀 Installation

### 1. Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv cam_env
source cam_env/bin/activate  # Linux/Mac
# cam_env\Scripts\activate   # Windows

# Install dependencies
pip install opencv-python numpy pyserial

# Install Ultralytics YOLOv8 (recommended for best results)
pip install ultralytics

# OR for faster CPU inference
pip install onnxruntime
```

### 2. ESP32/ESP8266 Setup

1. Open **Arduino IDE**
2. Install ESP32/ESP8266 board support:
   - **ESP32**: Tools → Board → Boards Manager → Search "ESP32" → Install
   - **ESP8266**: Tools → Board → Boards Manager → Search "ESP8266" → Install
3. Install **Servo Library** (usually built-in for ESP32/ESP8266)
4. Open `esp_servo_controller/esp_servo_controller.ino`
5. Select your board: Tools → Board → **ESP32 Dev Module** or **NodeMCU ESP8266**
6. Upload the sketch to your ESP

## 🎮 Usage

### Step 1: Upload ESP Code
1. Connect ESP32/ESP8266 to computer via USB
2. Open Arduino IDE
3. Load `esp_servo_controller/esp_servo_controller.ino`
4. Upload to board
5. Note the COM port (e.g., `/dev/ttyUSB0` or `COM3`)

### Step 2: Run Object Tracker

```bash
# Activate virtual environment
source cam_env/bin/activate  # Linux/Mac
# cam_env\Scripts\activate   # Windows

# Run the tracker
python yolo_object_tracker.py
```

### Step 3: Controls

| Key | Action |
|-----|--------|
| `q` | Quit the application |
| `ESC` | Alternative quit |

## ⚙️ Configuration

Edit the configuration section at the top of `yolo_object_tracker.py`:

```python
# Serial Communication
SERIAL_PORT = '/dev/ttyUSB0'  # Change to your ESP port
BAUD_RATE = 115200

# Camera Settings  
CAMERA_INDEX = 2  # 0, 1, or 2 depending on your webcam

# Servo Settings
BASE_PAN = 90      # Home horizontal position
BASE_TILT = 40     # Home vertical position

# Tracking Sensitivity
CONFIDENCE_THRESHOLD = 0.5  # Minimum detection confidence
KP_PAN = 0.03              # Pan proportional gain
KP_TILT = 0.03             # Tilt proportional gain
MAX_STEP = 2               # Max servo movement per frame
DEAD_ZONE = 20             # Center tolerance in pixels
```

## 📊 Supported Object Classes

With YOLOv8, the system can detect these 80 COCO classes:

```
person, bicycle, car, motorcycle, airplane, bus, train, truck, boat,
traffic light, fire hydrant, stop sign, parking meter, bench, bird, cat,
dog, horse, sheep, cow, elephant, bear, zebra, giraffe, backpack, umbrella,
handbag, tie, suitcase, frisbee, skis, snowboard, sports ball, kite,
baseball bat, baseball glove, skateboard, surfboard, tennis racket, bottle,
wine glass, cup, fork, knife, spoon, bowl, banana, apple, sandwich, orange,
broccoli, carrot, hot dog, pizza, donut, cake, chair, couch, potted plant,
bed, dining table, toilet, tv, laptop, mouse, remote, keyboard, cell phone,
microwave, oven, toaster, sink, refrigerator, book, clock, vase, scissors,
teddy bear, hair drier, toothbrush
```

## 🎯 How It Works

```
┌─────────────┐     USB      ┌─────────────────────┐    Serial    ┌──────────────┐
│   Webcam    │ ───────────► │  Python/YOLO/OpenCV │ ───────────► │   ESP32/8266 │
└─────────────┘              └─────────────────────┘              └──────────────┘
                                   │
                                   ▼
                          Detect objects & calculate
                          center position difference
                                   │
                                   ▼
                          Send servo commands to
                          center the largest object
                                   │
                                   ▼
                              ┌─────────┐
                              │  Servos │ ──► Pan/Tilt camera
                              └─────────┘
```

## 🔍 Detection & Tracking Logic

1. **Object Detection**: YOLO processes each frame and identifies objects with bounding boxes
2. **Object Selection**: System picks the **largest** detected object to track
3. **Center Calculation**: Computes center point of the selected object
4. **Error Calculation**: Determines offset from frame center
5. **Servo Movement**: Smoothly moves servos to reduce offset (PID-style control)
6. **Status Display**: Shows object name, accuracy %, and servo positions

## 🛠️ Troubleshooting

### Camera Issues
```python
# Try different camera indices
CAMERA_INDEX = 0  # Built-in webcam
CAMERA_INDEX = 1  # First external webcam
CAMERA_INDEX = 2  # Second external webcam
```

### Serial Connection Failed
```bash
# Linux - Check permissions
sudo usermod -aG dialout $USER
# Then logout/login

# Find correct port
ls /dev/ttyUSB*    # ESP devices
ls /dev/ttyACM*    # Some ESP devices
```

### Servo Not Moving
1. Check power supply (servos need ~5V, may need external power)
2. Verify pin connections
3. Test with servo test function in ESP code

### Low FPS
```python
# Use smaller YOLO model
# Replace 'yolov8n.pt' with 'yolov8s.pt' (small) or 'yolov8n.pt' (nano)
```

### Object Not Detected
```python
# Lower confidence threshold
CONFIDENCE_THRESHOLD = 0.3  # More detections
```

## 📝 ESP Serial Protocol

The ESP expects commands in this format:
```
Format: PAN,TILT\n
Example: 90,45\n

Range: 0-180 for both values
```

Response from ESP:
```
Target -> Pan: 90°, Tilt: 45°
```

## 🔄 Return to Base Position

When no object is detected for 2 seconds, the system automatically:
1. Returns servos to base position (PAN=90°, TILT=40°)
2. Displays "No Object - Returning to Base" status

## 📈 Performance Tips

| Optimization | Effect |
|--------------|--------|
| Use YOLOv8n (nano) | Fastest, good accuracy |
| Reduce frame size | 640×480 or 416×416 |
| Close other apps | More CPU resources |
| Use GPU (if available) | Faster inference |

## 🎨 Customization Options

### Track Specific Object Class Only
```python
# In detect_objects function, add filter:
TARGET_CLASS = "person"  # Track only people

if class_names[cls] == TARGET_CLASS:
    detections.append(...)
```

### Adjust Servo Range
```python
PAN_MIN, PAN_MAX = 10, 170    # Limit horizontal range
TILT_MIN, TILT_MAX = 20, 120  # Limit vertical range
```

### Change Colors
```python
# In draw_detections function:
color = (0, 255, 0)  # BGR format - Green
```

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## 📧 Support

If you have questions:
1. Check the troubleshooting section
2. Review your serial port settings
3. Verify hardware connections

---

**Happy Tracking!** 🎯

