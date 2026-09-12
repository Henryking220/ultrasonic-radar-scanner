#include <Servo.h>

const int TRIG_PIN = 7;
const int ECHO_PIN = 6;
const int SERVO_PIN = 9;

Servo radarServo;

int currentAngle = 90;
int scanStart = 0;
int scanEnd = 180;
int scanStep = 5;
int scanDelay = 120;

bool scanning = true;
bool locked = false;
unsigned long lastPausedScan = 0;

float getDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  long duration = pulseIn(ECHO_PIN, HIGH, 30000);
  if (duration == 0) return -1;
  return duration * 0.0343 / 2;
}

float getStableDistance() {
  float total = 0;
  int validReadings = 0;
  for (int i = 0; i < 3; i++) {
    float distance = getDistance();
    if (distance > 0) {
      total += distance;
      validReadings++;
    }
    delay(10);
  }
  if (validReadings == 0) return -1;
  return total / validReadings;
}

void sendReading() {
  float distance = getStableDistance();
  if (distance > 0) {
    Serial.print(currentAngle);
    Serial.print(",");
    Serial.println(distance, 1);
  }
}

void checkCommands() {
  if (!Serial.available()) return;
  String command = Serial.readStringUntil('\n');
  command.trim();

  if (command == "P") {
    scanning = false;
    locked = false;
    radarServo.write(currentAngle);
  }
  else if (command == "R") {
    locked = false;
    scanning = true;
  }
  else if (command == "H") {
    scanning = false;
    locked = false;
    currentAngle = 90;
    radarServo.write(currentAngle);
    delay(300);
    sendReading();
  }
  else if (command == "L") {
    scanning = false;
    locked = false;
    currentAngle -= 5;
    if (currentAngle < 0) currentAngle = 0;
    radarServo.write(currentAngle);
    delay(120);
    sendReading();
  }
  else if (command == "D") {
    scanning = false;
    locked = false;
    currentAngle += 5;
    if (currentAngle > 180) currentAngle = 180;
    radarServo.write(currentAngle);
    delay(120);
    sendReading();
  }
  else if (command.startsWith("A")) {
    int requestedAngle = command.substring(1).toInt();
    if (requestedAngle >= 0 && requestedAngle <= 180) {
      scanning = false;
      locked = true;
      currentAngle = requestedAngle;
      radarServo.write(currentAngle);
      delay(150);
      sendReading();
    }
  }
  else if (command.startsWith("G")) {
    String values = command.substring(1);
    int separator = values.indexOf(',');
    if (separator > 0) {
      int newStart = values.substring(0, separator).toInt();
      int newEnd = values.substring(separator + 1).toInt();
      if (newStart >= 0 && newStart <= 180 &&
          newEnd >= 0 && newEnd <= 180 &&
          newStart < newEnd) {
        scanStart = newStart;
        scanEnd = newEnd;
        currentAngle = scanStart;
        radarServo.write(currentAngle);
      }
    }
  }
  else if (command.startsWith("V")) {
    int newSpeed = command.substring(1).toInt();
    if (newSpeed >= 30 && newSpeed <= 1000) {
      scanDelay = newSpeed;
    }
  }
  else if (command.startsWith("Q")) {
    int newStep = command.substring(1).toInt();
    if (newStep >= 1 && newStep <= 10) {
      scanStep = newStep;
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  radarServo.attach(SERVO_PIN);
  radarServo.write(currentAngle);
  delay(500);
}

void loop() {
  checkCommands();

  if (scanning) {
    for (currentAngle = scanStart; currentAngle <= scanEnd; currentAngle += scanStep) {
      checkCommands();
      if (!scanning) break;
      radarServo.write(currentAngle);
      delay(scanDelay);
      sendReading();
      delay(10);
    }

    for (currentAngle = scanEnd; currentAngle >= scanStart; currentAngle -= scanStep) {
      checkCommands();
      if (!scanning) break;
      radarServo.write(currentAngle);
      delay(scanDelay);
      sendReading();
      delay(10);
    }
  }
  else {
    if (millis() - lastPausedScan >= 250) {
      lastPausedScan = millis();
      sendReading();
    }
    checkCommands();
  }
}
