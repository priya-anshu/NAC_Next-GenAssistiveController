import sys
import subprocess
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QRadioButton, QPushButton, QMessageBox, QInputDialog
)
from PyQt6.QtCore import Qt
from config.profile_manager import (
    get_profile, add_or_update_profile, set_default_profile
)

class SelectorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NAC – Next-Gen Assistive Controller")
        self.setFixedSize(360, 250)

        # Load default profile settings
        self.settings = get_profile("default")
        input_mode = self.settings.get("input_mode", "voice")

        # UI setup
        central = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        central.setLayout(layout)
        self.setCentralWidget(central)

        layout.addWidget(QLabel("Select Input Method:"))

        self.radio_voice   = QRadioButton("Voice Control Only")
        self.radio_gesture = QRadioButton("Gesture Control Only")
        self.radio_both    = QRadioButton("Both Voice & Gesture")

        # Pre-select based on profile
        if input_mode == "gesture":
            self.radio_gesture.setChecked(True)
        elif input_mode == "both":
            self.radio_both.setChecked(True)
        else:
            self.radio_voice.setChecked(True)

        layout.addWidget(self.radio_voice)
        layout.addWidget(self.radio_gesture)
        layout.addWidget(self.radio_both)

        btn_launch = QPushButton("Launch")
        btn_launch.clicked.connect(self.launch_selected)
        layout.addWidget(btn_launch)

        btn_profiles = QPushButton("Manage Profiles…")
        btn_profiles.clicked.connect(self.manage_profiles)
        layout.addWidget(btn_profiles)

    def manage_profiles(self):
        # Prompt for new profile name
        name, ok = QInputDialog.getText(self, "Profile Name", "Enter profile name:")
        if not (ok and name.strip()):
            return
        name = name.strip()

        # Capture current settings
        mode = ("voice" if self.radio_voice.isChecked()
                else "gesture" if self.radio_gesture.isChecked()
                else "both")
        new_settings = {
            "input_mode": mode,
            "click_threshold": self.settings.get("click_threshold", 30),
            "click_cooldown":  self.settings.get("click_cooldown", 0.5),
            "scroll_scale":    self.settings.get("scroll_scale", 2),
            "language":        self.settings.get("language", "en-US")
        }

        add_or_update_profile(name, new_settings)
        set_default_profile(name)
        QMessageBox.information(
            self, "Profile Saved",
            f"Profile '{name}' saved and set as default."
        )
        self.settings = new_settings

    def launch_selected(self):
        # Build command list based on selection
        commands = []
        mode = ("voice" if self.radio_voice.isChecked()
                else "gesture" if self.radio_gesture.isChecked()
                else "both")

        if mode in ("voice", "both"):
            commands.append(("Voice Module", [
                sys.executable,
                os.path.join("input_handlers", "voice_module.py")
            ]))
        if mode in ("gesture", "both"):
            commands.append(("Gesture Module", [
                sys.executable,
                os.path.join("input_handlers", "gesture_module.py")
            ]))

        # Launch each module
        for name, cmd in commands:
            try:
                subprocess.Popen(cmd)
            except Exception as e:
                QMessageBox.critical(self, "Error",
                    f"Failed to launch {name}:\n{e}")
                return

        launched = ", ".join(n for n, _ in commands)
        QMessageBox.information(self, "Launched",
                                f"{launched} started successfully.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SelectorWindow()
    window.show()
    sys.exit(app.exec())
