# TODO: Servo Tracking - Tilt Movement Fix

## Status: ✅ COMPLETE - FIXED TILT SERVO ISSUES

### Problems Fixed:
- Tilt servo not moving at all
- GPIO 4 may have PWM issues on ESP32
- Base tilt position 40° was at extreme for some servo setups

### Solution Applied:

**ESP32 Firmware (`esp_servo_controller/esp_servo_controller.ino`):**
- Changed TILT_SERVO_PIN: GPIO4 → GPIO13 (more reliable PWM)
- Changed BASE_TILT: 40° → 90° (center position)
- Changed BASE_PAN: 40° → 90° (center position)
- STEP_SIZE: 3 → 4
- UPDATE_DELAY: 25ms → 20ms
- EMA_ALPHA: 0.3 → 0.4

**Python Script (`yolo_object_tracker.py`):**
- BASE_TILT: 40 → 90 (matching ESP32)
- BASE_PAN: 90 (unchanged)
- PAN limits: 5-175
- TILT limits: 10-170

### Hardware Note:
**New Tilt Servo Pin: GPIO 13** (was GPIO 4)
- Re-wire your tilt servo to GPIO 13
- GPIO 4 may not support proper PWM on some ESP32 boards

### Expected Behavior:
- Both pan and tilt servos move
- Start at center position (90°, 90°)
- Full range of vertical movement
- Directions inverted (object up → camera looks down)

### To Test:
1. Re-wire tilt servo to GPIO 13
2. Re-upload ESP32 firmware
3. Run: `source .venv/bin/activate && python yolo_object_tracker.py`
4. Move object:
   - Left side → Pan moves right
   - Right side → Pan moves left
   - Top → Tilt moves down
   - Bottom → Tilt moves up

