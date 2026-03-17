import sys
import threading
import queue
import os
import contextlib
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import pyqtSignal, QObject, QTimer
from config import Config
from input_listener import InputListener
from audio_recorder import AudioRecorder
from inference_engine import InferenceEngine
from text_injector import TextInjector
from gui.tray_icon import WhisperTrayIcon
from gui.settings_window import SettingsWindow
from gui.overlay_window import OverlayWindow

@contextlib.contextmanager
def ignore_stderr():
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(sys.stderr.fileno())
    os.dup2(devnull, sys.stderr.fileno())
    try:
        yield
    finally:
        os.dup2(old_stderr, sys.stderr.fileno())
        os.close(devnull)
        os.close(old_stderr)

class AppState(QObject):
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()
    text_emitted = pyqtSignal(str)
    text_updated = pyqtSignal(str)

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    config = Config()
    state = AppState()
    
    audio_queue = queue.Queue()
    text_queue = queue.Queue()
    realtime_text_queue = queue.Queue()

    # Initialize components
    overlay = OverlayWindow()
    
    with ignore_stderr():
        recorder = AudioRecorder(config, audio_queue)
    
    inference = InferenceEngine(config, audio_queue, text_queue, realtime_text_queue)
    injector = TextInjector(config, text_queue)

    def on_press():
        print("\n[!] Triggered: Recording...")
        state.recording_started.emit()
        if config.get("show_overlay", True):
            overlay.set_text("Listening...", force_show=True)
        with ignore_stderr():
            recorder.start_recording()
        inference.set_recording(True)

    def on_release():
        print("[!] Released: Transcribing...")
        state.recording_stopped.emit()
        inference.set_recording(False)
        recorder.stop_recording()
        overlay.clear_and_hide()

    listener = InputListener(config, on_press, on_release)

    # Periodic check for real-time text
    def check_realtime():
        try:
            while True:
                text = realtime_text_queue.get_nowait()
                if config.get("show_overlay", True):
                    state.text_updated.emit(text)
        except queue.Empty:
            pass

    timer = QTimer()
    timer.timeout.connect(check_realtime)
    timer.start(50)

    # Signals
    state.text_updated.connect(overlay.set_text)

    # UI
    settings_window = SettingsWindow(config)
    tray = WhisperTrayIcon(state)
    tray.settings_action.triggered.connect(settings_window.show)
    settings_window.settings_saved.connect(listener.update_hotkey)
    settings_window.settings_saved.connect(listener.update_device)
    tray.show()

    # Start threads
    recorder.start()
    inference.start()
    injector.start()
    listener.start()

    print("Whisper-Wayland is running...")

    try:
        sys.exit(app.exec())
    finally:
        print("Shutting down...")
        listener.stop()
        recorder.stop()
        inference.stop()
        injector.stop()

if __name__ == "__main__":
    main()
