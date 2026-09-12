# 🔭 Ultrasonic Radar Scanner

A DIY Arduino-based ultrasonic radar and security monitoring system built around an **HC-SR04 ultrasonic sensor**, an **SG90 servo**, and an **Arduino UNO R3**. A Python desktop application turns the sensor readings into a live radar-style display with target tracking, alarms, and operator controls.

> **Current milestone:** Functional desktop ultrasonic radar/security prototype.

## 📸 Physical Build

The radar is built as a simple, no-solder breadboard prototype. The HC-SR04 is mounted on the SG90 servo so the sensor can sweep across the detection area.

<table>
<tr>
<td width="50%"><img src="./Ultrasonic%20Sensor%201.jpeg" alt="Ultrasonic Radar physical build 1" width="100%"></td>
<td width="50%"><img src="./Ultrasonic%20Sensor%202.jpeg" alt="Ultrasonic Radar physical build 2" width="100%"></td>
</tr>
</table>

## 🎥 Project Demo

The full project demonstration is available on YouTube.

▶️ **[Watch the Full Demo on YouTube](https://youtu.be/XmJOcAPssGY)**

The video demonstrates the physical radar build and its scanning operation. The original video is approximately **600 MB**, so it is hosted externally rather than stored directly in the GitHub repository.

## ✨ Features

- 0–180° servo scanning
- Configurable scan start/end angles
- Configurable scan step (1–10°)
- Configurable scan delay/speed
- HC-SR04 distance measurement
- Three-reading averaging for more stable measurements
- Live PC radar visualization
- Multiple software-tracked targets with IDs (T01, T02, ...)
- Target angle, distance, speed and movement status
- Warning and critical distance zones
- Audible PC alarm for close targets
- Target lock and servo positioning
- Play/pause scanning
- Manual left/right movement
- Home position at 90°
- Keyboard and GUI controls

## 🧰 Hardware

- Arduino UNO R3
- HC-SR04 ultrasonic sensor
- SG90 180° servo
- Breadboard
- Jumper wires
- USB cable
- Windows PC running Python

## 🔌 Wiring

### HC-SR04

| HC-SR04 | Arduino UNO |
|---|---|
| VCC | 5V |
| GND | GND |
| TRIG | D7 |
| ECHO | D6 |

### SG90 Servo

| Servo | Arduino UNO |
|---|---|
| Brown/Black | GND |
| Red | 5V |
| Orange/Yellow | D9 |

## 🗂️ Project Structure

```text
ultrasonic-radar-scanner/
├── Arduino/
│   └── UltrasonicRadar.ino
├── PC_Radar/
│   └── radar.py
├── Ultrasonic Sensor 1.jpeg
├── Ultrasonic Sensor 2.jpeg
├── README.md
└── requirements.txt
```

## ⚙️ How It Works

1. The SG90 rotates the HC-SR04 through the configured scan range.
2. At each angle, the ultrasonic sensor takes three readings and averages valid results.
3. Arduino sends `angle,distance` measurements over USB serial.
4. Python receives the measurements and renders the radar display.
5. The software groups nearby sequential detections into persistent target tracks.
6. Targets are assigned IDs and their movement is estimated from distance changes.
7. Close targets trigger warning/critical states and an audible PC alarm.
8. The operator can pause, resume, adjust the scan, or lock the servo onto a target.

## 🖥️ Python Radar Application

The desktop application uses **Tkinter** for the interface and **PySerial** for communication with the Arduino.

Install the dependency:

```bash
pip install -r requirements.txt
```

Then run the application from the `PC_Radar` directory:

```bash
cd PC_Radar
python radar.py
```

The current PC configuration expects the Arduino on **COM6** at **115200 baud**.

> Close Arduino Serial Monitor or any other program using COM6 before starting the Python application.

## 🎮 Controls

The application supports GUI controls and keyboard shortcuts.

| Control | Function |
|---|---|
| ▶ PLAY | Resume scanning |
| ⏸ PAUSE | Pause scanning |
| 🎯 LOCK TARGET | Lock onto a selected target |
| ◀ LEFT 5° | Move sensor left |
| 🏠 HOME 90° | Return to center |
| RIGHT 5° ▶ | Move sensor right |
| Space | Play/Pause |
| P | Pause |
| R | Resume |
| L | Left |
| D | Right |
| H | Home |
| T | Target lock |

## 📡 Arduino Serial Protocol

The Arduino communicates at **115200 baud**.

| Command | Function |
|---|---|
| `P` | Pause scanning |
| `R` | Resume scanning |
| `H` | Move to home position (90°) |
| `L` | Move left 5° |
| `D` | Move right 5° |
| `A<angle>` | Lock/move to a specific angle |
| `G<start>,<end>` | Set scan range |
| `V<delay>` | Set scan delay |
| `Q<step>` | Set scan step |

Example:

```text
G30,150
V100
Q5
A120
```

## 🚨 Detection & Alarm System

The PC radar uses distance zones to classify detections:

- **≤ 30 cm:** Critical / danger zone
- **≤ 50 cm:** Warning zone
- **> 50 cm:** Normal detection

Tracked targets can also be classified as **STATIONARY**, **APPROACHING**, **FAST APPROACH**, or **MOVING AWAY** based on changes in measured distance.

## ⚠️ Important Limitation

This is **not a true multi-target radar sensor**. The HC-SR04 measures one direction at a time while the servo sweeps. Multiple-target tracking is a software interpretation of sequential measurements, so targets that are close together can sometimes merge or create separate tracks.

The current system is also **local**: the Arduino is connected to the PC by USB. Remote phone monitoring would require a Wi-Fi-capable device such as an ESP32 and an internet-accessible dashboard.

## 🚀 Future Development

- ESP32 Wi-Fi connectivity
- Remote phone dashboard
- Internet-based live radar monitoring
- Phone notifications
- Better target tracking
- Event logging and scan statistics
- More robust alarm acknowledgement and lock management
- Improved physical enclosure/mounting

## 📚 Learning Goals

This project combines practical concepts from:

- Arduino programming
- Embedded systems
- Ultrasonic sensing
- Servo motor control
- Serial communication
- Python GUI development
- Real-time data visualization
- Basic target tracking
- Alarm/security system design

## 📄 License

This project is currently provided as a personal DIY/learning project.
