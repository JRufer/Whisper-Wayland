import pyaudio
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QLineEdit, QPushButton, QMessageBox, QSlider)
from PyQt6.QtCore import pyqtSignal, Qt
import evdev
from evdev import ecodes

class SettingsWindow(QWidget):
    settings_saved = pyqtSignal()

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setWindowTitle("Whisper Wayland Settings")
        self.setMinimumWidth(400)
        self.setLayout(QVBoxLayout())
        
        # Model Selection
        self.layout().addWidget(QLabel("Whisper Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["tiny", "base", "small", "medium", "large-v3"])
        self.model_combo.setCurrentText(self.config.get("model_size", "base"))
        self.layout().addWidget(self.model_combo)
        
        # Audio Device Selection
        self.layout().addWidget(QLabel("Audio Input Device:"))
        self.device_combo = QComboBox()
        self.populate_audio_devices()
        self.layout().addWidget(self.device_combo)

        # Keyboard Device Selection (evdev)
        self.layout().addWidget(QLabel("Keyboard Event Device (evdev):"))
        self.kbd_combo = QComboBox()
        self.populate_keyboard_devices()
        self.layout().addWidget(self.kbd_combo)

        # Microphone Boost (Gain)
        self.layout().addWidget(QLabel("Microphone Boost (Software Gain):"))
        gain_layout = QHBoxLayout()
        self.gain_slider = QSlider(Qt.Orientation.Horizontal)
        self.gain_slider.setRange(5, 50) # 0.5x to 5.0x
        # Value in config is float, e.g. 1.0. Slider uses ints.
        current_gain = self.config.get("mic_gain", 1.0)
        self.gain_slider.setValue(int(current_gain * 10))
        
        self.gain_label = QLabel(f"{current_gain:.1f}x")
        self.gain_slider.valueChanged.connect(lambda v: self.gain_label.setText(f"{v/10.0:.1f}x"))
        
        gain_layout.addWidget(self.gain_slider)
        gain_layout.addWidget(self.gain_label)
        self.layout().addLayout(gain_layout)
        
        # Hotkey Selection
        self.layout().addWidget(QLabel("Global Hotkey:"))
        h_layout = QHBoxLayout()
        self.hotkey_label = QLabel(", ".join(self.config.get("hotkey", ["KEY_LEFTMETA", "KEY_SPACE"])))
        self.hotkey_label.setStyleSheet("font-weight: bold; border: 1px solid #ccc; padding: 5px;")
        h_layout.addWidget(self.hotkey_label)
        
        self.record_btn = QPushButton("Record")
        self.record_btn.setCheckable(True)
        self.record_btn.clicked.connect(self.toggle_recording)
        h_layout.addWidget(self.record_btn)
        self.layout().addLayout(h_layout)
        
        # Recording state
        self.recorded_keys = set()
        self.is_recording_hotkey = False
        
        # Save/Cancel
        buttons = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        buttons.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.close)
        buttons.addWidget(cancel_btn)
        self.layout().addLayout(buttons)

    def populate_audio_devices(self):
        p = pyaudio.PyAudio()
        current_index = self.config.get("input_device_index")
        
        found_current = False
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info.get('maxInputChannels') > 0:
                name = info.get('name')
                self.device_combo.addItem(f"{i}: {name}", i)
                if current_index == i:
                    self.device_combo.setCurrentIndex(self.device_combo.count() - 1)
                    found_current = True
        
        p.terminate()

    def populate_keyboard_devices(self):
        current_path = self.config.get("evdev_device")
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        
        # Sort so keyboards are at the top
        devices.sort(key=lambda d: (ecodes.EV_KEY in d.capabilities() and ecodes.KEY_A in d.capabilities().get(ecodes.EV_KEY, [])), reverse=True)
        
        for dev in devices:
            if ecodes.EV_KEY in dev.capabilities():
                self.kbd_combo.addItem(f"{dev.name} ({dev.path})", dev.path)
                if current_path == dev.path:
                    self.kbd_combo.setCurrentIndex(self.kbd_combo.count() - 1)

    def toggle_recording(self):
        if self.record_btn.isChecked():
            self.is_recording_hotkey = True
            self.recorded_keys = set()
            self.hotkey_label.setText("Press keys... (Wait 1s after release)")
            self.record_btn.setText("Stop")
            self.grabKeyboard()
        else:
            self.stop_recording()

    def stop_recording(self):
        self.is_recording_hotkey = False
        self.record_btn.setChecked(False)
        self.record_btn.setText("Record")
        self.releaseKeyboard()
        if not self.recorded_keys:
            self.hotkey_label.setText(", ".join(self.config.get("hotkey")))

    def keyPressEvent(self, event):
        if self.is_recording_hotkey:
            # We need the evdev scancode name. 
            # Qt key codes are different, but we can try to map some or just use evdev directly.
            # Actually, grabbing keyboard in Qt doesn't give us scancodes easily.
            # A better way for Linux/Wayland to "record" is to temporarily listen to evdev.
            pass
        super().keyPressEvent(event)

    # Since we can't easily get raw scancodes from Qt keyPressEvent for all keys (like Meta),
    # let's use a simpler approach for now: allow typing them or a basic mapper.
    # OR: The user asked for "click record button and then press key combo".
    # I'll implement a simple Qt key mapper for common keys.
    
    def keyPressEvent(self, event):
        if self.is_recording_hotkey:
            key = event.key()
            # Map Qt keys to evdev KEY_ names
            mapping = {
                Qt.Key.Key_Meta: "KEY_LEFTMETA",
                Qt.Key.Key_Alt: "KEY_LEFTALT",
                Qt.Key.Key_Control: "KEY_LEFTCTRL",
                Qt.Key.Key_Shift: "KEY_LEFTSHIFT",
                Qt.Key.Key_Space: "KEY_SPACE",
                Qt.Key.Key_Enter: "KEY_ENTER",
                Qt.Key.Key_Return: "KEY_ENTER",
            }
            
            # For letters
            if Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
                key_name = f"KEY_{chr(key)}"
            else:
                key_name = mapping.get(key)
                if not key_name:
                    # Fallback to Qt name if possible
                    key_name = f"KEY_{event.text().upper()}" if event.text() else None
            
            if key_name:
                self.recorded_keys.add(key_name)
                self.hotkey_label.setText(", ".join(sorted(list(self.recorded_keys))))
        else:
            super().keyPressEvent(event)

    def save_settings(self):
        self.config.set("model_size", self.model_combo.currentText())
        
        # Audio device
        device_index = self.device_combo.currentData()
        self.config.set("input_device_index", device_index)

        # Keyboard device
        kbd_path = self.kbd_combo.currentData()
        self.config.set("evdev_device", kbd_path)
        
        # Hotkey
        if self.recorded_keys:
            self.config.set("hotkey", sorted(list(self.recorded_keys)))
        
        # Gain
        self.config.set("mic_gain", self.gain_slider.value() / 10.0)
        
        self.config.save()
        self.settings_saved.emit()
        QMessageBox.information(self, "Settings", "Settings saved and applied!")
        self.close()
