# ros_voicengesture_control
Voice and gesture control system based on ROS2 (Arduino, ESP32)
A multi-modal robot control system using ROS2 that combines voice commands and hand gesture recognition for intuitive robot control. Designed to work with Arduino and ESP32 microcontrollers!


## Overview

This system enables control of a mobile robot using:
- **Hand gestures** detected via webcam (MediaPipe)
- **Voice commands** (offline speech recognition with Vosk)
- **Command fusion** with configurable priority between inputs
- **Serial bridge** for communication with Arduino/ESP32


## Features

- Real-time hand gesture recognition using MediaPipe
- Offline voice command recognition with Vosk
- Intelligent command fusion with priority management
- Serial communication with Arduino/ESP32
- Webcam streaming via ROS2
- Fully configurable via ROS2 parameters
- Command timeout and cooldown mechanisms
- Real-time visualization and FPS display


## Prerequisites

### ROS2 Installation
- Ubuntu 20.04+ (Linux)
- ROS2 (tested on Humble)

### Python Dependencies
```bash
pip install -r requirements.txt
```


## System Dependencies 
```bash
# MediaPipe
pip install mediapipe

# Vosk for voice recognition
pip install vosk

# Sound device for audio capture
sudo apt-get install portaudio19-dev
pip install sounddevice

# OpenCV and ROS2 bridge
pip install opencv-python cv-bridge

# Serial communication
pip install pyserial

# Vosk model (download separately)
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip

```


## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ros2-voice-gesture-control.git
cd ros2-voice-gesture-control
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Download Vosk:
```bash
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip -d ~/
```

4. Make all scripts executable:
```bash
chmod +x *.py
```

5. Setup serial permissions (for ESP32/Arduino):
```bash
sudo usermod -a -G dialout $USER
# Re-login or reboot for changes to take effect
```


## Launch all nodes in separate terminals
Terminal 1:
```bash
python3 webcam_publisher.py
```
Terminal 2:
```bash
python3 webcam_publisher.py
```
Terminal 3:
```bash
python3 webcam_publisher.py
```
Terminal 4:
```bash
python3 webcam_publisher.py
```
Terminal 5:
```bash
python3 webcam_publisher.py
```

!!Launch all nodes with a single launch file (optional)


## Nodes Description


**1. webcam_publisher.py**
Purpose: Captures webcam video and publishes to ROS2

Publishes: webcam/image_raw (sensor_msgs/Image)

Parameters:

camera_id: Camera device ID (default: 0)

frame_width: Frame width (default: 640)

frame_height: Frame height (default: 480)

fps: Frames per second (default: 15)

show_window: Show preview window (default: True)

timeout_sec: Timeout before switching to test mode (default: 5)


**2. gesture_detector.py**
Purpose: Detects hand gestures using MediaPipe

Subscribes: webcam/image_raw

Publishes: gesture_cmd (std_msgs/String)

Parameters:

None (configured internally)

Gestures:

1 finger: Forward

2 fingers + thumb left: Turn Left

2 fingers + thumb right: Turn Right

Fist: Stop

Pinky only: Backward


**3. voice_recognizer.py**
Purpose: Recognizes voice commands using Vosk (offline)

Publishes: voice_cmd (std_msgs/String)

Parameters:

model_path: Path to Vosk model (default: 'vosk-model-small-en-us-0.15')

sample_rate: Audio sample rate (default: 16000)

blocksize: Audio block size (default: 8000)

Voice Commands:

"forward", "go", "walk", "ahead" → FORWARD

"stop", "halt", "neutral", "reset" → STOP

"left", "turn left" → TURN_LEFT

"right", "turn right" → TURN_RIGHT

"back", "backward", "reverse" → BACKWARD


**4. arduino_command_fusion.py**
Purpose: Fuses gesture and voice commands with priority

Subscribes: gesture_cmd, voice_cmd

Publishes: final_cmd, /cmd_vel (Twist)

Parameters:

priority: 'gesture' or 'voice' (default: 'gesture')

voice_timeout: Voice command timeout (default: 3.0s)

gesture_timeout: Gesture command timeout (default: 2.0s)

use_serial: Enable serial output (default: True)


**5. arduino_serial_bridge.py**
Purpose: Bridges Twist commands to serial for Arduino/ESP32

Subscribes: /cmd_vel (Twist)

Serial Output: Single-character commands: F, B, L, R, S

Parameters:

port: Serial port ('auto' for auto-detection)

baudrate: Baud rate (default: 115200)


## Gesture commands

👆 One finger (index)	- FORWARD	
🤞 Two fingers (index+middle) + tilt left - TURN_LEFT	
🤞 Two fingers (index+middle) + tilt right - TURN_RIGHT
✊ Fist (all fingers down) - STOP
🤙 Pinky only - BACKWARD


## Voice commands

"forward", "go" - FORWARD
"stop" - STOP
"left", "turn left" - TURN_LEFT
"right", "turn right" - TURN_RIGHT
"back", "backward" - BACKWARD


## Parameter Configuration

```bash
# Example: Change priority to voice
ros2 param set /arduino_command_fusion priority voice

# Example: Change camera ID
ros2 param set /webcam_publisher camera_id 1

# Example: Change voice timeout
ros2 param set /arduino_command_fusion voice_timeout 5.0
```

Modify the detect_simple_gesture() function in gesture_detector.py to add or change gestures!!
Modify the commands dictionary in voice_recognizer.py to add new voice commands!!


## Hardware setup!

The serial bridge expects a simple protocol:

F - Move forward

B - Move backward

L - Turn left

R - Turn right

S - Stop

Example Arduino code:

```bash
void setup() {
  Serial.begin(115200);
}

void loop() {
  if (Serial.available()) {
    char cmd = Serial.read();
    switch(cmd) {
      case 'F': moveForward(); break;
      case 'B': moveBackward(); break;
      case 'L': turnLeft(); break;
      case 'R': turnRight(); break;
      case 'S': stop(); break;
    }
  }
}
```

