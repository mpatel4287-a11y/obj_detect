/*
  YOLO Object Tracker - ESP32/ESP8266 Servo Controller
  Receives serial commands: "PAN,TILT\n" and controls SG90 servos
  
  Connections:
  - Pan Servo (Horizontal): GPIO 2 (or D2)
  - Tilt Servo (Vertical): GPIO 13 (or D13)
  
  Commands (send via Serial Monitor):
  - "P,angle" - Test pan servo (e.g., "P,90")
  - "T,angle" - Test tilt servo (e.g., "T,90")
  - "B,pan,tilt" - Set both servos (e.g., "B,90,90")
  - "S" - Sweep test both servos
*/

#include <ESP32Servo.h>

// ==================== CONFIGURATION ====================

// Servo pins
#ifdef ESP32
  #define PAN_SERVO_PIN 2    // GPIO2
  #define TILT_SERVO_PIN 13  // GPIO13
#else  // ESP8266
  #define PAN_SERVO_PIN 2    // D2
  #define TILT_SERVO_PIN 4   // D4
#endif

// Servo parameters
#define MIN_PULSE 500     // Minimum pulse width
#define MAX_PULSE 2500    // Maximum pulse width
#define SERVO_FREQUENCY 50

// ==================== GLOBAL VARIABLES ====================

Servo panServo;
Servo tiltServo;

int panAngle = 90;
int tiltAngle = 10;    // Changed base angle to center position
int targetPan = 90;
int targetTilt = 10;   // Changed base angle to center position

const int STEP_SIZE = 3;       // Degrees per update
const int UPDATE_DELAY = 25;   // ms between updates

// ==================== SETUP ====================

void setup() {
  Serial.begin(115200);
  Serial.println("\n========================================");
  Serial.println("YOLO Object Tracker - ESP Servo Controller");
  Serial.println("========================================");
  
  #ifdef ESP32
    panServo.setPeriodHertz(SERVO_FREQUENCY);
    tiltServo.setPeriodHertz(SERVO_FREQUENCY);
  #endif
  
  // Attach servos
  panServo.attach(PAN_SERVO_PIN, MIN_PULSE, MAX_PULSE);
  tiltServo.attach(TILT_SERVO_PIN, MIN_PULSE, MAX_PULSE);
  
  // Initialize servos
  panServo.write(90);    // Pan at center
  tiltServo.write(10);   // Tilt at 10 degrees (user requested)
  
  delay(500);
  
  Serial.println("Servos initialized: Pan=90°, Tilt=10°");
  Serial.println("Commands: P,angle | T,angle | B,pan,tilt | S (sweep)");
  Serial.println("========================================\n");
}

// ==================== MAIN LOOP ====================

void loop() {
  // Process normal tracking commands (format: "90,90\n")
  static String buffer = "";
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (buffer.length() > 0) {
        // Check if it's a test command (starts with P, T, B, or S)
        if (buffer.startsWith("P,") || buffer.startsWith("T,") || buffer.startsWith("B,") || buffer.startsWith("S")) {
          parseTestCommand(buffer);
        } else {
          // Normal tracking command
          parseTrackingCommand(buffer);
        }
        buffer = "";
      }
    } else if (c != '\r') {
      buffer += c;
    }
  }

  // Smooth movement towards target
  updateServos();

  delay(UPDATE_DELAY);
}

// ==================== FUNCTIONS ====================

void parseTrackingCommand(String cmd) {
  int commaIndex = cmd.indexOf(',');
  if (commaIndex == -1) {
    return; // Invalid format
  }

  String panStr = cmd.substring(0, commaIndex);
  String tiltStr = cmd.substring(commaIndex + 1);

  int panVal = panStr.toInt();
  int tiltVal = tiltStr.toInt();

  if (panVal >= 0 && panVal <= 180 && tiltVal >= 0 && tiltVal <= 180) {
    targetPan = panVal;
    targetTilt = tiltVal;
    panAngle = panVal;
    tiltAngle = tiltVal;
    panServo.write(panAngle);
    tiltServo.write(tiltAngle);
    Serial.print("📥 RECEIVED: ");
    Serial.print(panVal);
    Serial.print(",");
    Serial.println(tiltVal);
  }
}

void parseTestCommand(String cmd) {
  if (cmd.startsWith("P,")) {
    // Pan test: "P,90"
    String angleStr = cmd.substring(2);
    int angle = angleStr.toInt();
    panServo.write(angle);
    Serial.print("Pan test: ");
    Serial.println(angle);
    targetPan = angle;
    panAngle = angle;
  }
  else if (cmd.startsWith("T,")) {
    // Tilt test: "T,90"
    String angleStr = cmd.substring(2);
    int angle = angleStr.toInt();
    tiltServo.write(angle);
    Serial.print("Tilt test: ");
    Serial.println(angle);
    targetTilt = angle;
    tiltAngle = angle;
  }
  else if (cmd.startsWith("B,")) {
    // Both servos: "B,90,90"
    String params = cmd.substring(2);
    int commaIndex = params.indexOf(',');
    if (commaIndex != -1) {
      String panStr = params.substring(0, commaIndex);
      String tiltStr = params.substring(commaIndex + 1);
      int panVal = panStr.toInt();
      int tiltVal = tiltStr.toInt();
      panServo.write(panVal);
      tiltServo.write(tiltVal);
      Serial.print("Both test: Pan=");
      Serial.print(panVal);
      Serial.print(", Tilt=");
      Serial.println(tiltVal);
      targetPan = panVal;
      targetTilt = tiltVal;
      panAngle = panVal;
      tiltAngle = tiltVal;
    }
  }
  else if (cmd == "S") {
    // Sweep test
    Serial.println("Running sweep test...");
    for (int a = 30; a <= 150; a += 10) {
      panServo.write(a);
      tiltServo.write(a);
      delay(200);
    }
    for (int a = 150; a >= 30; a -= 10) {
      panServo.write(a);
      tiltServo.write(a);
      delay(200);
    }
    panServo.write(90);
    tiltServo.write(30);  // Reset to new base angle
    targetPan = 90;
    targetTilt = 30;
    panAngle = 90;
    tiltAngle = 30;
    Serial.println("Sweep complete. Reset to 90,30");
  }
}

void updateServos() {
  // Pan movement
  if (panAngle < targetPan) {
    panAngle = min(panAngle + STEP_SIZE, targetPan);
    panServo.write(panAngle);
  } else if (panAngle > targetPan) {
    panAngle = max(panAngle - STEP_SIZE, targetPan);
    panServo.write(panAngle);
  }
  
  // Tilt movement - ALWAYS update even if small change
  if (tiltAngle < targetTilt) {
    tiltAngle = min(tiltAngle + STEP_SIZE, targetTilt);
    tiltServo.write(tiltAngle);
  } else if (tiltAngle > targetTilt) {
    tiltAngle = max(tiltAngle - STEP_SIZE, targetTilt);
    tiltServo.write(tiltAngle);
  }
}

