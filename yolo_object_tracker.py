"""
YOLO Object Detection and Servo Tracking System
Detects objects, displays bounding boxes with accuracy,
and tracks the largest object using pan-tilt servos.

Hardware: ESP32/ESP8266 + SG90 Servos + Webcam
Optimized for old laptops with CPU-only processing
"""

import cv2
import serial
import time
import numpy as np

# ==================== CONFIGURATION ====================
# Serial Communication
SERIAL_PORTS = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyACM0', '/dev/ttyACM1']  # Try multiple ports
BAUD_RATE = 115200
SERIAL_TIMEOUT = 1
SERIAL_RETRIES = 3  # Number of retries for busy ports
RETRY_DELAY = 2     # Seconds to wait between retries

# Camera Settings - OPTIMIZED FOR OLD LAPTOPS
CAMERA_INDEX = 2  # Change to 0, 1, or 2 based on your webcam
FRAME_WIDTH = 320  # Reduced from 640 for much better CPU performance
FRAME_HEIGHT = 240 # Reduced from 480 for much better CPU performance
CAMERA_FPS = 15    # Reduced from 30 for better performance

# Performance Optimization for Old Laptops (CPU only)
SKIP_FRAMES = 2    # Skip every N frames (1 = process all, 2 = process every other, 3 = process 1 in 3)
CONFIDENCE_THRESHOLD = 0.6  # Higher threshold = fewer detections = faster processing

# Servo Settings
BASE_PAN = 90         # Horizontal center position (matching ESP32)
BASE_TILT = 30        # Vertical center position (changed to center)
PAN_MIN, PAN_MAX = 0, 180  # Full range for pan servo
TILT_MIN, TILT_MAX = 0, 180  # Full range for tilt servo

# Safe Zone Margins - Servos move ONLY when object crosses these boundaries
# Object inside safe zone → servos stay still
# Object outside safe zone → servos move to center the object
SAFE_ZONE_MARGIN = 20  # Safe zone margin from frame edges (pixels)

# Direct Tracking - When outside safe zone, move directly to center the object
SMOOTHING_FACTOR = 0.3  # Smooth movement (lower = smoother)
TILT_SENSITIVITY = 0.3  # Reduce tilt sensitivity (0.3 = very low sensitivity)

# Anti-Jitter Settings
DEAD_ZONE = 0        # No dead zone - respond immediately
SMOOTHING_WINDOW = 2 # Minimal smoothing
MAX_PAN = 175        # Maximum pan angle (prevent hitting limit)
MAX_TILT = 170       # Maximum tilt angle (use full range)
MIN_PAN = 5          # Minimum pan angle
MIN_TILT = 10        # Minimum tilt angle

# Performance
SEND_INTERVAL = 0.1  # Minimum time between serial commands (seconds) - faster
HEARTBEAT_INTERVAL = 1.0  # Send position every second even if unchanged

# Position Smoothing (Moving Average Filter)
SMOOTHING_WINDOW = 5  # Number of frames to average (higher = smoother movement)
DISPLAY_FPS = True   # Show FPS on screen
DEBUG_MODE = True    # Print debug info to console

# ==================== INITIALIZATION ====================

# Initialize Serial Communication
def init_serial():
    """Initialize serial connection to ESP - tries multiple ports with retries"""
    for port in SERIAL_PORTS:
        for attempt in range(SERIAL_RETRIES):
            try:
                ser = serial.Serial(port, BAUD_RATE, timeout=SERIAL_TIMEOUT)
                time.sleep(2)  # Allow ESP to reset
                print(f"✓ Connected to ESP on {port}")
                return ser
            except serial.SerialException as e:
                if "busy" in str(e).lower() or "resource busy" in str(e).lower():
                    print(f"Port {port} is busy (attempt {attempt + 1}/{SERIAL_RETRIES}). Retrying in {RETRY_DELAY}s...")
                    time.sleep(RETRY_DELAY)
                else:
                    print(f"✗ Failed to connect to {port}: {e}")
                    break  # Don't retry for other errors
            except Exception as e:
                print(f"✗ Unexpected error connecting to {port}: {e}")
                break

    print("✗ Serial connection failed on all ports")
    return None

# Initialize Camera
def init_camera():
    """Initialize webcam with optimized settings - tries multiple indices and backends"""
    # Try multiple camera indices (found by running find_camera.py)
    # Priority: External webcam (2) first, then laptop camera (0)
    camera_indices_to_try = [2, 0, 1]
    
    for cam_index in camera_indices_to_try:
        print(f"Trying camera index {cam_index}...", end=" ")
        
        # Try V4L2 backend first (Linux), then default
        backends_to_try = [
            (cv2.CAP_V4L2, "V4L2"),
            (cv2.CAP_GSTREAMER, "GStreamer"),
            (cv2.CAP_ANY, "Auto")
        ]
        
        for backend, backend_name in backends_to_try:
            try:
                cap = cv2.VideoCapture(cam_index, backend)
                
                if cap.isOpened():
                    # Test reading a frame
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        # Apply optimized settings
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
                        cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
                        
                        print(f"✓ SUCCESS with {backend_name}")
                        print(f"✓ Camera initialized (Index: {cam_index}, {FRAME_WIDTH}x{FRAME_HEIGHT} @ {CAMERA_FPS}fps, Backend: {backend_name})")
                        return cap
                    else:
                        print(f"✗ {backend_name} opened but can't read frame")
                        cap.release()
                else:
                    print(f"✗ {backend_name} failed to open")
            except Exception as e:
                print(f"✗ {backend_name} error: {e}")
                try:
                    cap.release()
                except:
                    pass
        
        print(f"Camera {cam_index} not available, trying next...")
    
    print("✗ No working camera found!")
    print("   Run 'python find_camera.py' to check available cameras")
    return None

# Initialize YOLO Model - OPTIMIZED FOR CPU
def init_yolo():
    """Initialize YOLOv8 model with CPU optimizations"""
    try:
        from ultralytics import YOLO
        # Use nano model and disable verbose output for faster processing
        model = YOLO('yolov8n.pt')
        # Set device to CPU explicitly
        model.to('cpu')
        # Disable augmentations for faster inference
        model.conf = CONFIDENCE_THRESHOLD
        print("✓ YOLOv8 model loaded (CPU mode)")
        return model, 'ultralytics'
    except ImportError:
        print("ultralytics not found, trying OpenCV DNN...")
        return init_yolo_opencv(), 'opencv'

def init_yolo_opencv():
    """Initialize YOLO using OpenCV DNN - CPU only"""
    # Use smaller model for better CPU performance
    yolo_cfg = 'models/deploy.prototxt'
    yolo_weights = 'models/mobilenet_iter_73000.caffemodel'
    
    try:
        net = cv2.dnn.readNetFromCaffe(yolo_cfg, yolo_weights)
        
        # Force CPU backend
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
        print("✓ OpenCV DNN model loaded (CPU mode)")
        
        # Define common classes for MobileNet-SSD
        class_names = ['background', 'aeroplane', 'bicycle', 'bird', 'boat',
                       'bottle', 'bus', 'car', 'cat', 'chair', 'cow',
                       'diningtable', 'dog', 'horse', 'motorbike', 'person',
                       'pottedplant', 'sheep', 'sofa', 'train', 'tvmonitor']
        
        return net, class_names
    except Exception as e:
        print(f"✗ YOLO loading failed: {e}")
        return None, None

# ==================== OBJECT DETECTION ====================

def detect_objects_ultralytics(frame, model):
    """Detect objects using ultralytics YOLOv8 - optimized"""
    try:
        # Use smaller image size and half precision for CPU
        results = model(frame, conf=CONFIDENCE_THRESHOLD, verbose=False, imgsz=320)
        detections = []
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Bounding box coordinates
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = box.conf[0].cpu().numpy()
                cls = int(box.cls[0].cpu().numpy())
                
                detections.append({
                    'bbox': (int(x1), int(y1), int(x2), int(y2)),
                    'conf': float(conf),
                    'cls': cls
                })
        
        return detections
    except Exception as e:
        print(f"Detection error: {e}")
        return []

def detect_objects_opencv(frame, net, classes):
    """Detect objects using OpenCV DNN - optimized for CPU"""
    if net is None:
        return []
    
    # Use smaller blob size for faster processing
    blob = cv2.dnn.blobFromImage(frame, 0.00784, (300, 300), (127.5, 127.5, 127.5), False)
    net.setInput(blob)
    
    # Get output
    detections = net.forward()
    
    results = []
    h, w = frame.shape[:2]
    
    # Process detections
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > CONFIDENCE_THRESHOLD:
            idx = int(detections[0, 0, i, 1])
            
            # Calculate bounding box
            box = detections[0, 0, i, 3:7] * [w, h, w, h]
            (x1, y1, x2, y2) = box.astype("int")
            
            results.append({
                'bbox': (x1, y1, x2, y2),
                'conf': float(confidence),
                'cls': idx
            })
    
    return results

# ==================== SERVO CONTROL ====================

def calculate_servo_positions(obj_bbox, frame_center, frame_size, current_pan, current_tilt):
    """
    Calculate new servo positions using DIRECT CENTERING tracking.

    - Object fully inside frame margins → servos stay still
    - Object partially outside frame margins → servos move directly to center the object

    Margins are defined by SAFE_ZONE_MARGIN from frame edges.
    """
    cx, cy = frame_center
    w, h = frame_size
    x1, y1, x2, y2 = obj_bbox

    # Calculate object center
    obj_center_x = (x1 + x2) // 2
    obj_center_y = (y1 + y2) // 2

    # Define frame margins (object must be fully inside these)
    margin_left = SAFE_ZONE_MARGIN
    margin_right = w - SAFE_ZONE_MARGIN
    margin_top = SAFE_ZONE_MARGIN
    margin_bottom = h - SAFE_ZONE_MARGIN

    # Check if object is partially outside frame margins
    obj_left_out = x1 < margin_left
    obj_right_out = x2 > margin_right
    obj_top_out = y1 < margin_top
    obj_bottom_out = y2 > margin_bottom

    # If object is fully inside margins, stay still
    if not (obj_left_out or obj_right_out or obj_top_out or obj_bottom_out):
        return current_pan, current_tilt

    # Object is partially outside - calculate angles to center it
    # Map frame position to servo angles
    # Frame center (cx, cy) = servo center (90, 90)
    # Frame edges = servo limits (0, 180)

    # Calculate required pan angle to center object horizontally
    if obj_center_x < cx:
        # Object left of center - pan right (increase angle)
        pan_ratio = obj_center_x / cx  # 0 at left edge, 1 at center
        target_pan = int(BASE_PAN + (PAN_MAX - BASE_PAN) * (1 - pan_ratio))
    else:
        # Object right of center - pan left (decrease angle)
        pan_ratio = (w - obj_center_x) / (w - cx)  # 1 at center, 0 at right edge
        target_pan = int(BASE_PAN - (BASE_PAN - PAN_MIN) * (1 - pan_ratio))

    # Calculate required tilt angle to center object vertically
    if obj_center_y < cy:
        # Object above center - tilt up (decrease angle)
        tilt_ratio = obj_center_y / cy  # 0 at top edge, 1 at center
        tilt_change = (BASE_TILT - TILT_MIN) * (1 - tilt_ratio) * TILT_SENSITIVITY
        target_tilt = int(BASE_TILT - tilt_change)
    else:
        # Object below center - tilt down (increase angle)
        tilt_ratio = (h - obj_center_y) / (h - cy)  # 1 at center, 0 at bottom edge
        tilt_change = (TILT_MAX - BASE_TILT) * (1 - tilt_ratio) * TILT_SENSITIVITY
        target_tilt = int(BASE_TILT + tilt_change)

    # Apply smoothing
    new_pan = current_pan + (target_pan - current_pan) * SMOOTHING_FACTOR
    new_tilt = current_tilt + (target_tilt - current_tilt) * SMOOTHING_FACTOR

    # Clamp to servo limits
    new_pan = max(PAN_MIN, min(PAN_MAX, int(round(new_pan))))
    new_tilt = max(TILT_MIN, min(TILT_MAX, int(round(new_tilt))))

    return new_pan, new_tilt


def apply_smoothing_filter(pan_positions, tilt_positions):
    """Apply moving average filter to smooth servo position history"""
    if len(pan_positions) < 2:
        return None, None
    
    smoothed_pan = sum(pan_positions) / len(pan_positions)
    smoothed_tilt = sum(tilt_positions) / len(tilt_positions)
    
    return int(round(smoothed_pan)), int(round(smoothed_tilt))

def send_servo_positions(ser, pan, tilt, last_send_time):
    """Send servo positions to ESP with rate limiting"""
    current_time = time.time()

    if current_time - last_send_time >= SEND_INTERVAL:
        try:
            command = f"{pan},{tilt}\n"
            ser.write(command.encode())
            print(f"📤 SENT: {pan},{tilt}")  # Debug: show sent commands
            last_send_time = current_time
        except Exception as e:
            print(f"Serial send error: {e}")

    return last_send_time

# ==================== DRAWING ====================

def draw_detections(frame, detections, class_names):
    """Draw bounding boxes and labels on frame - simplified for performance"""
    for det in detections:
        x1, y1, x2, y2 = det['bbox']
        conf = det['conf']
        cls = det['cls']
        
        # Get class name
        if cls < len(class_names):
            label = f"{class_names[cls]}: {conf*100:.0f}%"
        else:
            label = f"Obj: {conf*100:.0f}%"
        
        # Draw bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)
        
        # Draw label
        cv2.putText(frame, label, (x1, y1 - 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
    
    return frame

def draw_info(frame, pan, tilt, fps=None, status="Tracking"):
    """Draw status information on frame with safe zone indicator"""
    h, w = frame.shape[:2]
    
    # Draw safe zone boundary (50px margin)
    safe_left = SAFE_ZONE_MARGIN
    safe_right = w - SAFE_ZONE_MARGIN
    safe_top = SAFE_ZONE_MARGIN
    safe_bottom = h - SAFE_ZONE_MARGIN
    cv2.rectangle(frame, (safe_left, safe_top), (safe_right, safe_bottom), (0, 255, 255), 1)
    
    # Center crosshair
    cx, cy = w // 2, h // 2
    cv2.drawMarker(frame, (cx, cy), (0, 0, 255), cv2.MARKER_CROSS, 15, 1)
    
    # Status text
    status_color = (0, 255, 0) if status == "Tracking" else (0, 0, 255)
    cv2.putText(frame, f"Status: {status}", (5, 20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 1)
    
    cv2.putText(frame, f"Pan: {pan} Tilt: {tilt}", (5, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    if fps is not None:
        cv2.putText(frame, f"FPS: {fps:.1f}", (5, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    
    # Safe zone legend
    cv2.putText(frame, f"Cyan: Safe Zone ({SAFE_ZONE_MARGIN}px)", (5, h - 35), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
    cv2.putText(frame, "Servos move when object exits zone", (5, h - 20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    
    # Instructions
    cv2.putText(frame, "Press 'q' to quit", (w - 120, h - 10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (128, 128, 128), 1)
    
    return frame

# ==================== MAIN LOOP ====================

def main():
    print("=" * 50)
    print("YOLO Object Detection & Servo Tracking")
    print("CPU-Optimized for Old Laptops")
    print("=" * 50)
    
    # Initialize components
    ser = init_serial()
    cap = init_camera()
    model, model_type = init_yolo()
    
    if cap is None:
        print("Camera initialization failed!")
        return
    
    # Load class names
    if model_type == 'ultralytics':
        class_names = model.names
    else:
        class_names = ['background', 'aeroplane', 'bicycle', 'bird', 'boat', 
                       'bottle', 'bus', 'car', 'cat', 'chair', 'cow', 
                       'diningtable', 'dog', 'horse', 'motorbike', 'person', 
                       'pottedplant', 'sheep', 'sofa', 'train', 'tvmonitor']
    
    # Servo state
    pan = BASE_PAN
    tilt = BASE_TILT
    last_send_time = 0
    last_time = time.time()
    frame_count = 0
    
    # Position history for smoothing
    pan_history = []
    tilt_history = []
    
    # Frame counter and status
    frame_counter = 0
    status = "Starting"
    detections = []  # Store last known detections
    
    print("\nStarting tracking... Press 'q' to quit")
    print("-" * 50)
    
    while True:
        try:
            # Read frame
            ret, frame = cap.read()
            if not ret:
                print("Camera read failed! Retrying...")
                time.sleep(0.5)
                continue
        
            # Frame skipping for CPU performance
            frame_counter += 1
            should_process = (frame_counter % SKIP_FRAMES == 0)
            
            if not should_process:
                # Still update servos for smooth movement
                if ser and status == "Tracking":
                    last_send_time = send_servo_positions(ser, pan, tilt, last_send_time)
                
                # Draw and show frame without processing
                frame = draw_detections(frame, detections, class_names)
                frame = draw_info(frame, pan, tilt, None, status)
                cv2.imshow("YOLO Object Tracker", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue
            
            # Get frame dimensions
            h, w = frame.shape[:2]
            frame_center = (w // 2, h // 2)
            
            # Detect objects
            try:
                if model_type == 'ultralytics':
                    detections = detect_objects_ultralytics(frame, model)
                else:
                    detections = detect_objects_opencv(frame, model, class_names)
            except Exception as e:
                print(f"Detection error: {e}")
                detections = []
            
            # Process detections
            if len(detections) > 0:
                # Find largest object
                try:
                    largest = max(detections, key=lambda d: 
                                 (d['bbox'][2] - d['bbox'][0]) * 
                                 (d['bbox'][3] - d['bbox'][1]))
                    
                    x1, y1, x2, y2 = largest['bbox']
                    obj_center = ((x1 + x2) // 2, (y1 + y2) // 2)
                    ox, oy = obj_center
                    
                    # Calculate new servo positions using bounding box (object half outside = trigger)
                    raw_pan, raw_tilt = calculate_servo_positions(
                        largest['bbox'], frame_center, (w, h), pan, tilt
                    )
                    
                    # Debug output
                    if DEBUG_MODE:
                        obj_center_x = (x1 + x2) // 2
                        obj_center_y = (y1 + y2) // 2

                        # Check if object is inside or outside safe zone
                        safe_left = SAFE_ZONE_MARGIN
                        safe_right = w - SAFE_ZONE_MARGIN
                        safe_top = SAFE_ZONE_MARGIN
                        safe_bottom = h - SAFE_ZONE_MARGIN

                        in_safe_zone = (safe_left <= obj_center_x <= safe_right and
                                       safe_top <= obj_center_y <= safe_bottom)

                        zone_status = "✓ INSIDE" if in_safe_zone else "⚠ OUTSIDE"
                        print(f"Frame: {w}x{h} | Obj Center: ({obj_center_x}, {obj_center_y}) | Safe: L{safe_left}-R{safe_right} T{safe_top}-B{safe_bottom} | Zone: {zone_status} | Pan: {pan}° -> {raw_pan}° | Tilt: {tilt}° -> {raw_tilt}°")
                    
                    # Apply smoothing filter
                    pan_history.append(raw_pan)
                    tilt_history.append(raw_tilt)
                    
                    # Keep only last N positions
                    if len(pan_history) > SMOOTHING_WINDOW:
                        pan_history.pop(0)
                        tilt_history.pop(0)
                    
                    # Apply moving average
                    if len(pan_history) >= 2:
                        smoothed_pan, smoothed_tilt = apply_smoothing_filter(pan_history, tilt_history)
                        if smoothed_pan is not None:
                            pan, tilt = smoothed_pan, smoothed_tilt
                        else:
                            pan, tilt = raw_pan, raw_tilt
                    else:
                        pan, tilt = raw_pan, raw_tilt
                    
                    # Send to ESP
                    if ser:
                        last_send_time = send_servo_positions(ser, pan, tilt, last_send_time)
                    
                    status = "Tracking"
                except Exception as e:
                    print(f"Processing error: {e}")
                    status = "Error"
            else:
                # No objects detected - stay at current position
                pan_history.clear()
                tilt_history.clear()

                # Stay at current position, don't return to base
                status = "No Object - Holding Position"
            
            # Draw all detections
            frame = draw_detections(frame, detections, class_names)
            
            # Calculate FPS
            frame_count += 1
            current_time = time.time()
            fps = frame_count / (current_time - last_time)
            if frame_count >= 30:
                frame_count = 0
                last_time = current_time
            
            # Draw info
            frame = draw_info(frame, pan, tilt, fps if DISPLAY_FPS else None, status)
            
            # Show frame
            cv2.imshow("YOLO Object Tracker", frame)
            
            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        except KeyboardInterrupt:
            print("\nInterrupted by user")
            break
        except Exception as e:
            print(f"Main loop error: {e}")
            time.sleep(0.5)
            continue
    
    # Cleanup
    if ser:
        ser.write(f"{BASE_PAN},{BASE_TILT}\n".encode())
        ser.close()
    
    cap.release()
    cv2.destroyAllWindows()
    print("\nTracking stopped. Goodbye!")

# ==================== ENTRY POINT ====================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")

