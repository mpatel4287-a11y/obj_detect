import cv2
import serial
import time

# ---------------- SERIAL ----------------
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
time.sleep(2)  # allow ESP reset

# ---------------- CAMERA ----------------
cap = cv2.VideoCapture(2)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# ---------------- FACE DETECTOR ----------------
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

# ---------------- SERVO BASE ----------------
BASE_PAN = 90
BASE_TILT = 40   # IMPORTANT: your required vertical base

PAN = BASE_PAN
TILT = BASE_TILT

# ---------------- CONTROL ----------------
KP = 0.03
MAX_STEP = 2
DEAD_ZONE = 25

SEND_INTERVAL = 0.1  # 10 Hz (CRITICAL)
last_send_time = 0

# ---------------- LOOP ----------------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5,
        minSize=(60, 60)
    )

    now = time.time()

    if len(faces) > 0:
        # pick largest face
        x, y, fw, fh = max(faces, key=lambda b: b[2] * b[3])

        fx = x + fw // 2
        fy = y + fh // 2

        err_x = fx - cx
        err_y = fy - cy

        # -------- PAN --------
        if abs(err_x) > DEAD_ZONE:
            PAN += max(-MAX_STEP, min(MAX_STEP, KP * err_x))

        # -------- TILT --------
        # screen Y increases downward
        if abs(err_y) > DEAD_ZONE:
            TILT -= max(-MAX_STEP, min(MAX_STEP, KP * err_y))

        PAN = int(max(0, min(180, PAN)))
        TILT = int(max(0, min(180, TILT)))

        # -------- SEND SLOWLY --------
        if now - last_send_time > SEND_INTERVAL:
            ser.write(f"{PAN},{TILT}\n".encode())
            last_send_time = now

        # -------- DRAW --------
        cv2.rectangle(frame, (x, y), (x + fw, y + fh), (0, 255, 0), 2)
        cv2.circle(frame, (fx, fy), 5, (255, 0, 0), -1)
        cv2.putText(frame, "FACE",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (0, 255, 0), 2)

    else:
        # -------- NO FACE → RETURN TO BASE --------
        PAN = BASE_PAN
        TILT = BASE_TILT

        if now - last_send_time > SEND_INTERVAL:
            ser.write(f"{PAN},{TILT}\n".encode())
            last_send_time = now

        cv2.putText(frame, "NO FACE",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (0, 0, 255), 2)

    # center marker
    cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

    cv2.imshow("Face Following (Stable)", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
ser.close()
cv2.destroyAllWindows()
