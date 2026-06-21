NeuroSpector: Open-Source AOI System 🔬

NeuroSpector is a low-cost (~$72 / 6000 INR), open-source Automated Optical Inspection (AOI) system for Printed Circuit Boards (PCBs). It combines custom 3D-printed gantry robotics, edge-microcontrollers, and a YOLOv8m deep learning model to detect missing PCB components in real-time.

🚀 Features

Real-Time Detection: 13.0 ms inference speed (~76 FPS) powered by NVIDIA CUDA.

Exceptional Accuracy: Achieved 0.995 mAP@0.5 with zero false positives across 8 defect classes.

Cyber-Industrial UI: Built with PyQt6, featuring an asynchronous hardware terminal and dynamic warning HUD.

Hybrid Architecture: Uses a smartphone IP camera (Samsung S23 Ultra ISOCELL HP2) to eliminate gantry cable drag, while an ESP32 handles hard-real-time motor limits.

🛠️ Hardware Requirements

Microcontroller: ESP32 Development Board

Actuation: MG996R Continuous Rotation Servo + GT2 Timing Belt

Driver: PCA9685 I2C PWM Driver (with external 5V 3A power supply)

Safety: 2x Mechanical Limit Switches

Camera: Any IP Webcam app (Smartphone) or USB camera

💻 Installation (Windows & Linux)

1. Clone the repository

git clone [https://github.com/YOUR_USERNAME/NeuroSpector.git](https://github.com/YOUR_USERNAME/NeuroSpector.git)
cd NeuroSpector


2. Create a Virtual Environment

# Windows
python -m venv yolo_env
yolo_env\Scripts\activate

# Linux/macOS
python3 -m venv yolo_env
source yolo_env/bin/activate


3. Install Dependencies

pip install -r requirements.txt


🎮 Running the System

We have included a pre-flight diagnostic launcher that verifies your environment, checks for the ESP32 connection, and boots the UI safely.

python neuro_launcher.py


(Note: If the ESP32 is not connected, the system will automatically fall back to Simulation Mode).

🧠 Pre-Trained Model

The repository includes our fully trained YOLOv8 Medium weights (best.pt) inside runs/detect/train/weights/. It is trained to detect 8 missing components on an Arduino Uno (ATmega, Crystal Oscillator, Analog/Digital Pins, etc.).

📝 License

Distributed under the MIT License. See LICENSE for more information.