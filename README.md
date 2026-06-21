NeuroSpector

NeuroSpector is an open-source, ultra-low-cost Automated Optical Inspection (AOI) system designed for Printed Circuit Board (PCB) quality control.

Commercial AOI machines frequently exceed $10,000 USD. This project provides a highly accurate, reproducible alternative for approximately 6,000 INR (~$72 USD) by combining a custom 3D-printed linear gantry, edge microcontrollers, and a YOLOv8m deep learning model.

⚙️ Core Architecture

The system utilizes a hybrid communication loop to achieve real-time, zero-lag inspection without introducing mechanical cable drag on the moving gantry:

Vision Node: A local IP camera stream (prototyped with a Samsung ISOCELL HP2 sensor) acts as the wireless optical feed.

Compute Node: A central machine (running an NVIDIA RTX 3050 Ti) processes the OpenCV video stream through a YOLOv8m model at 13.0ms per frame (~76 FPS).

Control Node: An ESP32 connected via USB Serial handles hard-real-time motor pulses and processes mechanical limit switch interrupts independently of the host OS.

🧰 Hardware Bill of Materials (BOM)

Component

Function

ESP32 Dev Module

Main control logic and serial communication

PCA9685 Driver

I2C PWM generation (isolates motor current)

MG996R Servo

Modified for 360° continuous rotation

GT2 Timing Belt & Pulley

Linear actuation for the camera carriage


Mechanical Limit Switches
(Add a demo GIF or image of the UI/Gantry here in the future)
Closed-loop boundary detection (x2)


5V 3A Power Supply

Dedicated power for the motor driver

3D Printed Parts / Rails

Structural gantry framework


🚀 Installation

The software stack is cross-platform and will automatically detect your OS (Windows, Linux, or macOS) and active serial ports.

1. Clone the repository

git clone [https://github.com/YOUR_USERNAME/NeuroSpector.git](https://github.com/YOUR_USERNAME/NeuroSpector.git)
cd NeuroSpector


2. Setup a Python Virtual Environment

For Windows:

python -m venv yolo_env
yolo_env\Scripts\activate


For Linux / macOS:

python3 -m venv yolo_env
source yolo_env/bin/activate


3. Install Dependencies(Add a demo GIF or image of the UI/Gantry here in the future)

pip install -r requirements.txt


💻 Usage

We have included a pre-flight diagnostic launcher that verifies your environment, auto-detects your connected ESP32 (COM or /dev/ttyUSB), and boots the PyQt6 Cyber-Industrial Dashboard.

python ns_launch.py


Note: If the ESP32 is not connected, the system will automatically fall back to Simulation Mode, allowing you to use the UI and test the AI without the physical hardware gantry.

Just want to test the AI model?

If you don't want to run the full UI and just want to see the model detect defects on test images (or via your webcam), please refer to our beginner-friendly guide: how_to_check_trained_model.txt.

🧠 Model Performance

The included best.pt model was trained to detect missing surface-mount devices and headers across 8 defect classes. Aggressive photometric and morphological augmentations were applied to the dataset to simulate factory vibrations and varying illumination.

mAP@0.5: 0.995

Precision: 0.981

Recall: 1.000

False Positives: 0 (Evaluated on validation matrix)

📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
