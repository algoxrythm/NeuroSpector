import os
import sys
import cv2
import serial
import time
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel,
                             QPushButton, QVBoxLayout, QHBoxLayout, QTextEdit,
                             QMessageBox, QFrame, QDialog, QLineEdit, QInputDialog,
                             QGraphicsDropShadowEffect, QSizePolicy)
from PyQt6.QtGui import QImage, QPixmap, QFont, QColor, QPalette
from ultralytics import YOLO

# =============================================================================
# --- CYBER-INDUSTRIAL PALETTE ---
# =============================================================================
BG_BASE = "#0B0F19"          # Deep Slate Void
PANEL_BG = "#111827"         # Elevated Panel Background
PANEL_BORDER = "#1F2937"     # Subtle panel border
ACCENT_CYAN = "#0DF5E3"      # Primary High-Tech Accent
ACCENT_CYAN_DIM = "#0BE0CF"  # Hover variant
WARN_AMBER = "#F59E0B"       # Alert/Warning Color
DANGER_RED = "#EF4444"       # Hard Stop / Error Colorns_launch.py
DANGER_RED_DIM = "#450A0A"   # Danger hover fillns_launch.py
TEXT_PRIMARY = "#F3F4F6"     # Bright White for main text
TEXT_MUTED = "#9CA3AF"       # Gray for secondary info
LOG_DIM = "#4B5563"          # Timestamp gray in terminal

# --- HARDWARE DEFAULTS ---
SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200
MODEL_PATH = "runs/detect/train/weights/best.pt"

# --- VIDEO CANVAS LOCK (fixes the infinite expansion bug) ---
VIDEO_W = 800
VIDEO_H = 600


def add_glow(widget, color=ACCENT_CYAN, blur=28, alpha=110, offset=0):
    """Attaches a soft drop-shadow 'glow' effect to a widget for a premium feel."""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    qc = QColor(color)
    qc.setAlpha(alpha)
    effect.setColor(qc)
    effect.setOffset(offset, offset)
    widget.setGraphicsEffect(effect)
    return effect


def build_dark_palette():
    """
    A handful of native widgets (QLineEdit/QMessageBox/QInputDialog on some
    OS themes) read text/background colors from the QPalette rather than
    fully honoring QSS. Without this, the dialog can render with mismatched
    native colors -> the 'glitchy' look and the invisible IP text. This is
    applied together with app.setStyle('Fusion') so QSS is honored
    consistently across platforms.
    """
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(BG_BASE))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Base, QColor(BG_BASE))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(PANEL_BG))
    palette.setColor(QPalette.ColorRole.Text, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(TEXT_MUTED))
    palette.setColor(QPalette.ColorRole.Button, QColor(PANEL_BG))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(PANEL_BG))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT_CYAN))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(BG_BASE))
    return palette


# =============================================================================
# --- GLOBAL STYLESHEET (applied at the QApplication level) ---
# =============================================================================
GLOBAL_STYLESHEET = f"""
QWidget {{
    font-family: 'Consolas', 'Roboto Mono', 'Segoe UI', monospace;
    color: {TEXT_PRIMARY};
}}

QMainWindow, QDialog {{
    background-color: {BG_BASE};
}}

QWidget#CentralWidget {{
    background-color: {BG_BASE};
}}

/* ---------- Panels / Cards ---------- */
QFrame#Panel {{
    background-color: {PANEL_BG};
    border: 1px solid {PANEL_BORDER};
    border-radius: 10px;
}}

QFrame#VideoContainer {{
    background-color: #000000;
    border: 2px solid {PANEL_BORDER};
    border-radius: 6px;
}}

/* ---------- Labels ---------- */
QLabel {{
    background: transparent;
}}

QLabel#SectionTitle {{
    color: {ACCENT_CYAN};
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 2px;
}}

QLabel#SubLabel {{
    color: {TEXT_MUTED};
    font-size: 12px;
}}

QLabel#BootTag {{
    color: {TEXT_MUTED};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 3px;
}}

QLabel#DialogTitle {{
    color: {ACCENT_CYAN};
    font-size: 19px;
    font-weight: 800;
    letter-spacing: 1px;
}}

QLabel#FpsLabel {{
    color: {WARN_AMBER};
    font-weight: 700;
    font-size: 13px;
    background-color: rgba(245, 158, 11, 0.08);
    border: 1px solid rgba(245, 158, 11, 0.35);
    border-radius: 5px;
    padding: 3px 10px;
}}

QLabel#VideoLabel {{
    color: {TEXT_MUTED};
    font-size: 13px;
    letter-spacing: 1px;
}}

QLabel#LiveDot {{
    color: {ACCENT_CYAN};
    font-size: 13px;
}}

/* ---------- Buttons ---------- */
QPushButton#PrimaryButton {{
    background-color: {ACCENT_CYAN};
    color: {BG_BASE};
    font-weight: 800;
    font-size: 14px;
    letter-spacing: 1px;
    border: none;
    border-radius: 6px;
    padding: 12px;
}}
QPushButton#PrimaryButton:hover {{
    background-color: {ACCENT_CYAN_DIM};
}}
QPushButton#PrimaryButton:pressed {{
    background-color: #09B3A6;
}}

QPushButton#ConnectButton {{
    background-color: {ACCENT_CYAN};
    color: {BG_BASE};
    font-weight: 800;
    font-size: 14px;
    letter-spacing: 1px;
    border: none;
    border-radius: 6px;
    padding: 12px;
}}
QPushButton#ConnectButton:hover {{
    background-color: {ACCENT_CYAN_DIM};
}}
QPushButton#ConnectButton:pressed {{
    background-color: #09B3A6;
}}

QPushButton#GhostButton {{
    background-color: transparent;
    color: {TEXT_MUTED};
    font-weight: 700;
    font-size: 12px;
    letter-spacing: 1px;
    border: 1px solid #374151;
    border-radius: 6px;
    padding: 10px;
}}
QPushButton#GhostButton:hover {{
    background-color: {PANEL_BORDER};
    color: {TEXT_PRIMARY};
    border: 1px solid {ACCENT_CYAN};
}}
QPushButton#GhostButton:pressed {{
    background-color: #0A0F1A;
}}

QPushButton#CaptureButton {{
    background-color: transparent;
    color: {ACCENT_CYAN};
    font-weight: 700;
    font-size: 12px;
    letter-spacing: 1px;
    border: 1px solid {ACCENT_CYAN};
    border-radius: 6px;
    padding: 10px;
}}
QPushButton#CaptureButton:hover {{
    background-color: rgba(13, 245, 227, 0.12);
    color: {TEXT_PRIMARY};
}}
QPushButton#CaptureButton:pressed {{
    background-color: rgba(13, 245, 227, 0.25);
}}

QPushButton#DangerButton {{
    background-color: transparent;
    color: {DANGER_RED};
    font-weight: 800;
    font-size: 12px;
    letter-spacing: 1px;
    border: 1px solid {DANGER_RED};
    border-radius: 6px;
    padding: 10px;
}}
QPushButton#DangerButton:hover {{
    background-color: {DANGER_RED_DIM};
    color: {TEXT_PRIMARY};
}}
QPushButton#DangerButton:pressed {{
    background-color: #2A0505;
}}

/* ---------- Inputs ---------- */
QLineEdit#ConnectionInput {{
    background-color: {BG_BASE};
    border: 1px solid {PANEL_BORDER};
    color: {TEXT_PRIMARY};
    padding: 11px 12px;
    border-radius: 6px;
    font-size: 13px;
    selection-background-color: {ACCENT_CYAN};
    selection-color: {BG_BASE};
}}
QLineEdit#ConnectionInput:focus {{
    border: 1px solid {ACCENT_CYAN};
}}

/* ---------- Terminal / Log ---------- */
QTextEdit#Terminal {{
    background-color: #05080A;
    border: 1px solid {PANEL_BORDER};
    border-radius: 6px;
    color: {TEXT_PRIMARY};
    font-size: 12px;
    padding: 10px;
}}
QTextEdit#Terminal QScrollBar:vertical {{
    background: {PANEL_BG};
    width: 8px;
    margin: 2px;
}}
QTextEdit#Terminal QScrollBar::handle:vertical {{
    background: {ACCENT_CYAN};
    border-radius: 4px;
    min-height: 24px;
}}
QTextEdit#Terminal QScrollBar::add-line:vertical, QTextEdit#Terminal QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* ---------- Message Boxes ---------- */
QMessageBox {{
    background-color: {PANEL_BG};
}}
QMessageBox QLabel {{
    color: {TEXT_PRIMARY};
    font-size: 13px;
}}
QMessageBox QPushButton {{
    background-color: transparent;
    color: {TEXT_PRIMARY};
    border: 1px solid {ACCENT_CYAN};
    border-radius: 5px;
    padding: 6px 16px;
    min-width: 90px;
}}
QMessageBox QPushButton:hover {{
    background-color: {ACCENT_CYAN};
    color: {BG_BASE};
}}

/* ---------- Input Dialog (NS Mode count prompt) ---------- */
QInputDialog {{
    background-color: {PANEL_BG};
}}
QInputDialog QLabel {{
    color: {TEXT_PRIMARY};
    font-size: 13px;
}}
QInputDialog QSpinBox {{
    background-color: {BG_BASE};
    border: 1px solid {PANEL_BORDER};
    border-radius: 5px;
    padding: 6px;
    color: {TEXT_PRIMARY};
}}
QInputDialog QPushButton {{
    background-color: transparent;
    color: {TEXT_PRIMARY};
    border: 1px solid {ACCENT_CYAN};
    border-radius: 5px;
    padding: 6px 16px;
    min-width: 80px;
}}
QInputDialog QPushButton:hover {{
    background-color: {ACCENT_CYAN};
    color: {BG_BASE};
}}
"""


class ConnectionDialog(QDialog):
    """Custom Startup Dialog to fetch the IP Camera URL"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SYSTEM BOOT")
        self.setFixedSize(480, 280)
        self.setModal(True)
        self.ip_address = None

        layout = QVBoxLayout()
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(10)

        boot_tag = QLabel("// SYSTEM BOOT SEQUENCE")
        boot_tag.setObjectName("BootTag")
        layout.addWidget(boot_tag)

        title = QLabel("OPTICAL SENSOR UPLINK")
        title.setObjectName("DialogTitle")
        layout.addWidget(title)

        desc = QLabel("Enter the IP Webcam stream address to bind the gantry's optical sensor.")
        desc.setObjectName("SubLabel")
        desc.setWordWrap(True)
        layout.addSpacing(6)
        layout.addWidget(desc)

        layout.addSpacing(14)

        self.input_ip = QLineEdit("http://192.168.1.15:8080/video")
        self.input_ip.setObjectName("ConnectionInput")
        self.input_ip.setMinimumHeight(38)
        # setText() moves the cursor to the end of the string, which made the
        # field appear to show only the tail of the URL ("...0/video") rather
        # than the full address. Resetting the cursor fixes that.
        self.input_ip.setCursorPosition(0)
        layout.addWidget(self.input_ip)

        layout.addSpacing(18)

        btn_connect = QPushButton("ESTABLISH CONNECTION  ▸")
        btn_connect.setObjectName("ConnectButton")
        btn_connect.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_connect.setMinimumHeight(46)
        btn_connect.clicked.connect(self.accept_connection)
        add_glow(btn_connect, ACCENT_CYAN, blur=24, alpha=90)
        layout.addWidget(btn_connect)

        hint = QLabel("Press ESC to abort boot sequence")
        hint.setObjectName("SubLabel")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        self.setLayout(layout)

    def accept_connection(self):
        self.ip_address = self.input_ip.text().strip()
        self.accept()


class NeuroSpectorUI(QMainWindow):
    def __init__(self, camera_url):
        super().__init__()
        self.setWindowTitle("NeuroSpector - Industrial AOI Terminal")
        self.setGeometry(100, 100, 1440, 880)
        self.setMinimumSize(1380, 820)

        self.camera_url = camera_url
        self.auto_mode = "IDLE"
        self.last_defect_log_time = {}
        self.last_frame = None       # most recent raw camera frame
        self.last_annotated_frame = None  # most recent frame with AI overlays drawn
        self.ns_target = 0           # NS Mode: number of units to capture
        self.ns_counter = 0          # NS Mode: units captured so far
        self.manual_capture_counter = 0  # Manual "Capture" button: shots taken so far

        # Initialize Engines
        self.init_ai()
        self.init_hardware()

        # Connect Optical Feed
        self.cap = cv2.VideoCapture(self.camera_url)
        # Keep the buffer shallow so the feed stays near real-time instead of
        # drifting behind on slow networks / IP webcam links.
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.init_ui()

        # Start Engine Loop
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_system)
        self.timer.start(30)

    def init_ai(self):
        try:
            self.model = YOLO(MODEL_PATH)
            self.ai_online = True
        except Exception:
            self.model = None
            self.ai_online = False

    def init_hardware(self):
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.05)
            self.hardware_online = True
        except Exception:
            self.ser = None
            self.hardware_online = False

    def init_ui(self):
        main_widget = QWidget()
        main_widget.setObjectName("CentralWidget")
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)

        # ================= LEFT PANEL: OPTICAL CANVAS =================
        left_panel = QFrame()
        left_panel.setObjectName("Panel")
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(18, 18, 18, 18)
        left_layout.setSpacing(14)

        header_layout = QHBoxLayout()
        live_dot = QLabel("●")
        live_dot.setObjectName("LiveDot")
        header_layout.addWidget(live_dot)

        cam_title = QLabel("LIVE SENSOR FEED  //  ISOCELL HP2")
        cam_title.setObjectName("SectionTitle")
        header_layout.addWidget(cam_title)
        header_layout.addStretch()

        self.lbl_fps = QLabel("FPS: --")
        self.lbl_fps.setObjectName("FpsLabel")
        header_layout.addWidget(self.lbl_fps)
        left_layout.addLayout(header_layout)

        # Fixed-size canvas: prevents the OpenCV frame injection from ever
        # forcing the window (or this panel) to expand uncontrollably.
        self.video_container = QFrame()
        self.video_container.setObjectName("VideoContainer")
        self.video_container.setFixedSize(VIDEO_W, VIDEO_H)
        self.video_container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        vid_layout = QVBoxLayout()
        vid_layout.setContentsMargins(0, 0, 0, 0)

        self.video_label = QLabel("AWAITING VIDEO STREAM...")
        self.video_label.setObjectName("VideoLabel")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vid_layout.addWidget(self.video_label)
        self.video_container.setLayout(vid_layout)

        # Center the fixed-size canvas inside the panel rather than stretching it.
        video_wrap = QHBoxLayout()
        video_wrap.addStretch()
        video_wrap.addWidget(self.video_container)
        video_wrap.addStretch()
        left_layout.addLayout(video_wrap)
        left_layout.addStretch()
        left_panel.setLayout(left_layout)

        # ================= RIGHT PANEL: TELEMETRY & CONTROL =================
        right_container = QWidget()
        right_container.setMinimumWidth(420)
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(24)

        # 1. System Vital Signs
        status_frame = QFrame()
        status_frame.setObjectName("Panel")
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(16, 16, 16, 16)
        status_layout.setSpacing(12)

        self.lbl_hw = self.create_status_badge("GANTRY CORE", self.hardware_online)
        self.lbl_ai = self.create_status_badge("VISION AI", self.ai_online)

        status_layout.addWidget(self.lbl_hw)
        status_layout.addWidget(self.lbl_ai)
        status_frame.setLayout(status_layout)
        right_layout.addWidget(status_frame)

        # 2. Terminal Matrix
        term_frame = QFrame()
        term_frame.setObjectName("Panel")
        term_layout = QVBoxLayout()
        term_layout.setContentsMargins(18, 18, 18, 18)
        term_layout.setSpacing(10)

        term_title = QLabel("SYSTEM EVENT LOG")
        term_title.setObjectName("SectionTitle")
        term_layout.addWidget(term_title)

        self.terminal = QTextEdit()
        self.terminal.setObjectName("Terminal")
        self.terminal.setReadOnly(True)
        self.log_event("NEUROSPECTOR SYSTEM INITIALIZED", "INFO")
        self.log_event(f"TARGET IP: {self.camera_url}", "INFO")

        term_layout.addWidget(self.terminal)
        term_frame.setLayout(term_layout)
        right_layout.addWidget(term_frame, 1)

        # 3. Control Deck
        ctrl_frame = QFrame()
        ctrl_frame.setObjectName("Panel")
        ctrl_layout = QVBoxLayout()
        ctrl_layout.setContentsMargins(18, 18, 18, 18)
        ctrl_layout.setSpacing(14)

        ctrl_title = QLabel("MANUAL OVERRIDE DECK")
        ctrl_title.setObjectName("SectionTitle")
        ctrl_layout.addWidget(ctrl_title)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        self.btn_rev = self.create_action_button("◂ REVERSE", self.manual_reverse)
        self.btn_stop = self.create_action_button("[ HALT ]", self.manual_stop, is_danger=True)
        self.btn_fwd = self.create_action_button("FORWARD ▸", self.manual_forward)

        btn_layout.addWidget(self.btn_rev)
        btn_layout.addWidget(self.btn_stop)
        btn_layout.addWidget(self.btn_fwd)
        ctrl_layout.addLayout(btn_layout)

        self.btn_capture = QPushButton("📷  CAPTURE IMAGE")
        self.btn_capture.setObjectName("CaptureButton")
        self.btn_capture.setMinimumHeight(40)
        self.btn_capture.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_capture.clicked.connect(self.manual_capture)
        ctrl_layout.addWidget(self.btn_capture)

        self.btn_auto = QPushButton("ENGAGE AUTO-SWEEP")
        self.btn_auto.setObjectName("PrimaryButton")
        self.btn_auto.setMinimumHeight(46)
        self.btn_auto.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_auto.clicked.connect(self.trigger_auto_mode)
        add_glow(self.btn_auto, ACCENT_CYAN, blur=22, alpha=70)
        ctrl_layout.addWidget(self.btn_auto)

        ctrl_frame.setLayout(ctrl_layout)
        right_layout.addWidget(ctrl_frame)

        right_container.setLayout(right_layout)

        main_layout.addWidget(left_panel, 0)
        main_layout.addWidget(right_container, 1)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.last_time = time.time()

    # --- UI FACTORY METHODS ---
    def create_status_badge(self, text, is_ok):
        dot = "●" if is_ok else "○"
        status_word = "ONLINE" if is_ok else "OFFLINE"
        lbl = QLabel(f"{dot}  {text}\n{status_word}")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        color = ACCENT_CYAN if is_ok else DANGER_RED
        bg = "rgba(13, 245, 227, 0.07)" if is_ok else "rgba(239, 68, 68, 0.07)"
        lbl.setStyleSheet(f"""
            background-color: {bg};
            border: 1px solid {color};
            color: {color};
            font-weight: 700;
            font-size: 12px;
            padding: 10px;
            border-radius: 6px;
        """)
        return lbl

    def create_action_button(self, text, callback, is_danger=False):
        btn = QPushButton(text)
        btn.setObjectName("DangerButton" if is_danger else "GhostButton")
        btn.setMinimumHeight(42)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(callback)
        return btn

    def log_event(self, text, level="INFO"):
        timestamp = time.strftime("%H:%M:%S")
        if level == "INFO":
            color, icon = ACCENT_CYAN, "▸"
        elif level == "WARN":
            color, icon = WARN_AMBER, "⚠"
        elif level == "ERROR":
            color, icon = DANGER_RED, "✕"
        else:
            color, icon = TEXT_PRIMARY, "·"

        msg = (f"<span style='color: {LOG_DIM};'>[{timestamp}]</span> "
               f"<span style='color: {color};'>{icon} [{level}] {text}</span>")
        self.terminal.append(msg)
        scrollbar = self.terminal.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    # --- HARDWARE CONTROLS ---
    def send_cmd(self, cmd):
        if self.hardware_online:
            self.ser.write(cmd.encode())
        else:
            self.log_event(f"SIM: Command '{cmd}' bypassed (No Hardware)", "WARN")

    def manual_forward(self):
        self.auto_mode = "IDLE"
        self.send_cmd('F')
        self.log_event("ACTUATOR DIR: FORWARD", "INFO")

    def manual_reverse(self):
        self.auto_mode = "IDLE"
        self.send_cmd('R')
        self.log_event("ACTUATOR DIR: REVERSE", "INFO")

    def manual_stop(self):
        self.auto_mode = "IDLE"
        self.send_cmd('S')
        self.log_event("EMERGENCY OVERRIDE: HALT", "ERROR")

    def manual_capture(self):
        """Saves the current camera frame (with AI defect overlays drawn in)
        to disk on demand, independent of any auto-sweep mode."""
        if self.last_annotated_frame is None:
            self.log_event("MANUAL CAPTURE FAILED - NO FRAME AVAILABLE", "WARN")
            return

        os.makedirs("ns_manual_captures", exist_ok=True)
        self.manual_capture_counter += 1
        filename = f"ns_manual_captures/manual_{self.manual_capture_counter:03d}.jpg"
        cv2.imwrite(filename, self.last_annotated_frame)
        self.log_event(f"MANUAL CAPTURE #{self.manual_capture_counter} -> {filename}", "INFO")

    def trigger_auto_mode(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("AUTO-SWEEP PROTOCOL")
        msg_box.setText("Select an automated inspection mode:")

        btn_single = msg_box.addButton("Single Pass", QMessageBox.ButtonRole.ActionRole)
        btn_continuous = msg_box.addButton("Continuous", QMessageBox.ButtonRole.ActionRole)
        btn_ns = msg_box.addButton("NS Mode", QMessageBox.ButtonRole.ActionRole)
        msg_box.addButton("Abort", QMessageBox.ButtonRole.RejectRole)

        msg_box.exec()
        clicked = msg_box.clickedButton()

        if clicked == btn_single:
            self.start_single_pass()
        elif clicked == btn_continuous:
            self.start_continuous()
        elif clicked == btn_ns:
            self.start_ns_mode()

    def start_single_pass(self):
        """Single Pass: home to the LEFT limit first, then sweep to the
        RIGHT limit, then halt."""
        self.auto_mode = "ONE_PASS_HOME_LEFT"
        self.log_event("INITIATING: SINGLE PASS - HOMING TO LEFT LIMIT", "INFO")
        self.send_cmd('R')

    def start_continuous(self):
        """Continuous: oscillate left<->right indefinitely until HALT is pressed."""
        self.auto_mode = "CONTINUOUS_RIGHT"
        self.log_event("INITIATING: CONTINUOUS SCAN ALGORITHM", "INFO")
        self.send_cmd('F')

    def start_ns_mode(self):
        """NS Mode: ask how many units to test, then alternate left/right
        limit hits, capturing a photo and incrementing the counter on every
        hit until the requested count is reached."""
        count, ok = QInputDialog.getInt(
            self, "NS MODE SETUP", "Number of Arduinos / PCBs to test:",
            value=1, min=1, max=999
        )
        if not ok:
            self.log_event("NS MODE SETUP ABORTED", "WARN")
            return

        self.ns_target = count
        self.ns_counter = 0
        self.auto_mode = "NS_TO_LEFT"
        self.log_event(f"NS MODE ENGAGED - TARGET: {count} UNIT(S)", "INFO")
        self.send_cmd('R')

    def handle_feedback(self, incoming):
        if "LIMIT_RIGHT" in incoming:
            self.log_event("BOUNDARY REACHED: RIGHT", "WARN")
            self.on_limit_hit("RIGHT")
        elif "LIMIT_LEFT" in incoming:
            self.log_event("BOUNDARY REACHED: LEFT", "WARN")
            self.on_limit_hit("LEFT")

    def on_limit_hit(self, side):
        """Central state machine for all three auto-sweep modes, called
        whenever a limit switch reports a hit."""

        # --- Single Pass: left-home, then right-sweep, then stop ---
        if self.auto_mode == "ONE_PASS_HOME_LEFT" and side == "LEFT":
            self.auto_mode = "ONE_PASS_SWEEP_RIGHT"
            self.log_event("HOME COMPLETE. SWEEPING TO RIGHT LIMIT.", "INFO")
            self.send_cmd('F')

        elif self.auto_mode == "ONE_PASS_SWEEP_RIGHT" and side == "RIGHT":
            self.auto_mode = "IDLE"
            self.send_cmd('S')
            self.log_event("SINGLE PASS COMPLETE. STANDBY.", "INFO")

        # --- Continuous: bounce between limits until manually stopped ---
        elif self.auto_mode == "CONTINUOUS_RIGHT" and side == "RIGHT":
            self.auto_mode = "CONTINUOUS_LEFT"
            self.send_cmd('R')

        elif self.auto_mode == "CONTINUOUS_LEFT" and side == "LEFT":
            self.auto_mode = "CONTINUOUS_RIGHT"
            self.send_cmd('F')

        # --- NS Mode: capture + count on every alternating limit hit ---
        elif self.auto_mode == "NS_TO_LEFT" and side == "LEFT":
            self.capture_ns_snapshot("LEFT")

        elif self.auto_mode == "NS_TO_RIGHT" and side == "RIGHT":
            self.capture_ns_snapshot("RIGHT")

    def capture_ns_snapshot(self, side):
        """Saves the most recent AI-annotated camera frame, increments the
        NS Mode counter, and either reverses direction for the next unit or
        stops once the target count is reached."""
        self.ns_counter += 1

        if self.last_annotated_frame is not None:
            os.makedirs("ns_captures", exist_ok=True)
            filename = f"ns_captures/unit_{self.ns_counter:03d}_{side}.jpg"
            cv2.imwrite(filename, self.last_annotated_frame)
            self.log_event(
                f"NS CAPTURE #{self.ns_counter}/{self.ns_target} [{side}] -> {filename}", "INFO"
            )
        else:
            self.log_event(
                f"NS CAPTURE #{self.ns_counter}/{self.ns_target} [{side}] - NO FRAME AVAILABLE", "WARN"
            )

        if self.ns_counter >= self.ns_target:
            self.auto_mode = "IDLE"
            self.send_cmd('S')
            self.log_event(f"NS MODE COMPLETE - {self.ns_counter} UNIT(S) CAPTURED.", "INFO")
        elif side == "LEFT":
            self.auto_mode = "NS_TO_RIGHT"
            self.send_cmd('F')
        else:
            self.auto_mode = "NS_TO_LEFT"
            self.send_cmd('R')

    # --- PROCESS ENGINE ---
    def update_system(self):
        # FPS Calculation
        current_time = time.time()
        fps = 1.0 / (current_time - self.last_time)
        self.last_time = current_time
        self.lbl_fps.setText(f"FPS: {int(fps)}")

        # Hardware Feedback
        if self.hardware_online and self.ser.in_waiting > 0:
            try:
                # errors='ignore' guards against corrupted USB bytes crashing the UI
                incoming = self.ser.readline().decode(errors='ignore').strip()
                if incoming:
                    self.handle_feedback(incoming)
            except Exception:
                pass

        # Optical Stream
        ret, frame = self.cap.read()
        if not ret:
            return

        # Cache the latest raw frame (annotated version is cached further
        # below once the AI pass runs). Feedback is processed above, before
        # this tick's frame exists, so captures use the previous tick's
        # frame -- at most ~30ms old, which is irrelevant since the gantry
        # is at a limit/stationary at that moment.
        self.last_frame = frame.copy()

        defect_found = False

        if self.ai_online:
            results = self.model(frame, verbose=False)[0]
            annotated_frame = results.plot()

            for box in results.boxes:
                class_name = self.model.names[int(box.cls[0])]
                defect_found = True

                if class_name not in self.last_defect_log_time or (current_time - self.last_defect_log_time[class_name] > 3.0):
                    self.log_event(f"ANOMALY: {class_name.upper()}", "ERROR")
                    self.last_defect_log_time[class_name] = current_time
        else:
            annotated_frame = frame

        # Cache the annotated (defect-overlay) frame so capture buttons save
        # what the AI actually saw, not the bare raw image.
        self.last_annotated_frame = annotated_frame

        # Dynamic Visual Alarms (border pulses amber on detection)
        if defect_found:
            self.video_container.setStyleSheet(
                f"QFrame#VideoContainer {{ border: 3px solid {WARN_AMBER}; border-radius: 6px; background-color: #000000; }}"
            )
        else:
            self.video_container.setStyleSheet(
                f"QFrame#VideoContainer {{ border: 2px solid {PANEL_BORDER}; border-radius: 6px; background-color: #000000; }}"
            )

        # Render OpenCV to PyQt
        rgb_image = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

        # The canvas is locked to a fixed VIDEO_W x VIDEO_H size, so scaling
        # always targets that constant rather than a size that could grow.
        scaled_pixmap = QPixmap.fromImage(qt_img).scaled(
            VIDEO_W - 4, VIDEO_H - 4,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.video_label.setPixmap(scaled_pixmap)

    def closeEvent(self, event):
        self.cap.release()
        if self.hardware_online:
            self.ser.write(b'S')
            self.ser.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Native OS styles (windowsvista, macOS, etc.) frequently fight with
    # custom QSS -- this is what caused the dialog flicker/glitch and the
    # IP text rendering invisible. Forcing Fusion + an explicit dark
    # palette makes every widget honor the stylesheet consistently across
    # platforms.
    app.setStyle("Fusion")
    app.setPalette(build_dark_palette())
    app.setStyleSheet(GLOBAL_STYLESHEET)

    # 1. Launch Connection Dialog First
    dialog = ConnectionDialog()
    if dialog.exec() == QDialog.DialogCode.Accepted:
        target_url = dialog.ip_address

        # 2. If user provided IP, launch main window
        if target_url:
            window = NeuroSpectorUI(target_url)
            window.show()
            sys.exit(app.exec())
    else:
        sys.exit(0)  # Exit if they close the dialog without connecting