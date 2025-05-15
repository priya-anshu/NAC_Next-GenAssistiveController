import sys
import os

# ─── Ensure project root is on sys.path ────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# ────────────────────────────────────────────────────────────────────────────

import subprocess
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QRadioButton,
    QPushButton,
    QMessageBox,
    QInputDialog,
    QDialog,
    QFormLayout,
    QSpinBox,
    QDoubleSpinBox,
    QComboBox,
    QDialogButtonBox
)
from PyQt6.QtCore import Qt
from config.profile_manager import (
    get_profile,
    add_or_update_profile,
    set_default_profile,
    update_default_profile
)

class SelectorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NAC – Next-Gen Assistive Controller")
        self.setFixedSize(360, 420)

        # Load default profile settings
        self.settings = get_profile("default")
        input_mode = self.settings.get("input_mode", "voice")

        # Build UI
        central = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        central.setLayout(layout)
        self.setCentralWidget(central)

        layout.addWidget(QLabel("Select Input Method:"))

        self.radio_voice   = QRadioButton("Voice Control Only")
        self.radio_gesture = QRadioButton("Gesture Control Only")
        self.radio_eye     = QRadioButton("Eye Control Only")
        self.radio_both    = QRadioButton("Hybrid (Voice + Gesture + Eye)")

        # Pre-select based on profile
        if input_mode == "gesture":
            self.radio_gesture.setChecked(True)
        elif input_mode == "eye":
            self.radio_eye.setChecked(True)
        elif input_mode == "both":
            self.radio_both.setChecked(True)
        else:
            self.radio_voice.setChecked(True)

        layout.addWidget(self.radio_voice)
        layout.addWidget(self.radio_gesture)
        layout.addWidget(self.radio_eye)
        layout.addWidget(self.radio_both)

        btn_launch   = QPushButton("Launch")
        btn_settings = QPushButton("Settings…")
        btn_profiles = QPushButton("Manage Profiles…")

        btn_launch.clicked.connect(self.launch_selected)
        btn_settings.clicked.connect(self.open_settings)
        btn_profiles.clicked.connect(self.manage_profiles)

        layout.addWidget(btn_launch)
        layout.addWidget(btn_settings)
        layout.addWidget(btn_profiles)

    def open_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Calibration & Language Settings")
        form = QFormLayout(dialog)

        # Gesture settings
        spin_click = QSpinBox()
        spin_click.setRange(1, 200)
        spin_click.setValue(self.settings.get("click_threshold", 30))
        form.addRow("Click Threshold (px):", spin_click)

        spin_cooldown = QDoubleSpinBox()
        spin_cooldown.setRange(0.1, 5.0)
        spin_cooldown.setSingleStep(0.1)
        spin_cooldown.setValue(self.settings.get("click_cooldown", 0.5))
        form.addRow("Click Cooldown (s):", spin_cooldown)

        spin_scroll = QSpinBox()
        spin_scroll.setRange(1, 10)
        spin_scroll.setValue(self.settings.get("scroll_scale", 2))
        form.addRow("Scroll Sensitivity:", spin_scroll)

        # Eye settings
        spin_eye_smooth = QSpinBox()
        spin_eye_smooth.setRange(1, 20)
        spin_eye_smooth.setValue(self.settings.get("eye_smoothing", 5))
        form.addRow("Eye Smoothing (frames):", spin_eye_smooth)

        spin_eye_sens = QDoubleSpinBox()
        spin_eye_sens.setRange(0.5, 5.0)
        spin_eye_sens.setSingleStep(0.1)
        spin_eye_sens.setValue(self.settings.get("eye_sensitivity", 2.0))
        form.addRow("Eye Sensitivity:", spin_eye_sens)

        # Language selector
        combo_lang = QComboBox()
        languages = [("English", "en-US"), ("Hindi", "hi-IN")]
        for name, code in languages:
            combo_lang.addItem(name, code)
        curr_code = self.settings.get("language", "en-US")
        idx = next((i for i, (_, c) in enumerate(languages) if c == curr_code), 0)
        combo_lang.setCurrentIndex(idx)
        form.addRow("Voice Language:", combo_lang)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Save all settings back to profile
            self.settings["click_threshold"] = spin_click.value()
            self.settings["click_cooldown"]  = spin_cooldown.value()
            self.settings["scroll_scale"]    = spin_scroll.value()
            self.settings["eye_smoothing"]   = spin_eye_smooth.value()
            self.settings["eye_sensitivity"] = spin_eye_sens.value()
            self.settings["language"]        = combo_lang.currentData()
            update_default_profile(self.settings)
            QMessageBox.information(
                self,
                "Settings Saved",
                "Calibration & language settings updated."
            )

    def manage_profiles(self):
        name, ok = QInputDialog.getText(
            self, "Profile Name", "Enter new profile name:"
        )
        if not (ok and name.strip()):
            return
        name = name.strip()

        mode = ("voice" if self.radio_voice.isChecked()
                else "gesture" if self.radio_gesture.isChecked()
                else "eye" if self.radio_eye.isChecked()
                else "both")
        new_settings = {
            "input_mode":      mode,
            "click_threshold": self.settings["click_threshold"],
            "click_cooldown":  self.settings["click_cooldown"],
            "scroll_scale":    self.settings["scroll_scale"],
            "eye_smoothing":   self.settings["eye_smoothing"],
            "eye_sensitivity": self.settings["eye_sensitivity"],
            "language":        self.settings["language"]
        }
        add_or_update_profile(name, new_settings)
        set_default_profile(name)
        QMessageBox.information(
            self,
            "Profile Saved",
            f"Profile '{name}' saved and set as default."
        )
        self.settings = new_settings

    def launch_selected(self):
        commands = []
        mode = ("voice" if self.radio_voice.isChecked()
                else "gesture" if self.radio_gesture.isChecked()
                else "eye" if self.radio_eye.isChecked()
                else "both")

        if mode == "voice":
            commands.append(("Voice Module", [
                sys.executable,
                os.path.join("input_handlers", "voice_module.py")
            ]))
        elif mode == "gesture":
            commands.append(("Gesture Module", [
                sys.executable,
                os.path.join("input_handlers", "gesture_module.py")
            ]))
        elif mode == "eye":
            commands.append(("Eye Module", [
                sys.executable,
                os.path.join("input_handlers", "eye_module.py")
            ]))
        else:  # hybrid
            commands.append(("Combined Module", [
                sys.executable,
                os.path.join("input_handlers", "combined_module.py")
            ]))

        for name, cmd in commands:
            try:
                subprocess.Popen(cmd)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to launch {name}:\n{e}"
                )
                return

        launched = ", ".join(n for n, _ in commands)
        QMessageBox.information(
            self,
            "Launched",
            f"{launched} started successfully."
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SelectorWindow()
    window.show()
    sys.exit(app.exec())
