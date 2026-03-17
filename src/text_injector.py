import evdev
from evdev import ecodes, UInput
import threading
import queue
import time
import pyperclip
import subprocess
import os

class TextInjector(threading.Thread):
    def __init__(self, config, text_queue):
        super().__init__(daemon=True)
        self.config = config
        self.text_queue = text_queue
        self.running = True
        self.ui = None
        self.last_text = ""

    def setup_uinput(self):
        try:
            # We need to define which keys our virtual keyboard can emit
            keys = [
                ecodes.KEY_LEFTCTRL, ecodes.KEY_V, 
                ecodes.KEY_LEFTSHIFT, ecodes.KEY_INSERT,
                ecodes.KEY_SPACE, ecodes.KEY_ENTER,
                ecodes.KEY_A, ecodes.KEY_B, ecodes.KEY_C, ecodes.KEY_D, ecodes.KEY_E,
                ecodes.KEY_F, ecodes.KEY_G, ecodes.KEY_H, ecodes.KEY_I, ecodes.KEY_J,
                ecodes.KEY_K, ecodes.KEY_L, ecodes.KEY_M, ecodes.KEY_N, ecodes.KEY_O,
                ecodes.KEY_P, ecodes.KEY_Q, ecodes.KEY_R, ecodes.KEY_S, ecodes.KEY_T,
                ecodes.KEY_U, ecodes.KEY_V, ecodes.KEY_W, ecodes.KEY_X, ecodes.KEY_Y,
                ecodes.KEY_Z, ecodes.KEY_0, ecodes.KEY_1, ecodes.KEY_2, ecodes.KEY_3,
                ecodes.KEY_4, ecodes.KEY_5, ecodes.KEY_6, ecodes.KEY_7, ecodes.KEY_8,
                ecodes.KEY_9, ecodes.KEY_COMMA, ecodes.KEY_DOT, ecodes.KEY_SLASH,
                ecodes.KEY_SEMICOLON, ecodes.KEY_APOSTROPHE, ecodes.KEY_LEFTBRACE,
                ecodes.KEY_RIGHTBRACE, ecodes.KEY_BACKSLASH, ecodes.KEY_MINUS,
                ecodes.KEY_EQUAL, ecodes.KEY_BACKSPACE, ecodes.KEY_TAB
            ]
            cap = { ecodes.EV_KEY: keys }
            self.ui = UInput(cap, name="Whisper-Wayland-Injector")
            print("Virtual keyboard created.")
        except Exception as e:
            print(f"Failed to create uinput device: {e}")

    def inject_text(self, text):
        if not text or text == self.last_text:
            return
        
        new_text = text
        if text.startswith(self.last_text):
            new_text = text[len(self.last_text):]
        
        if not new_text.strip():
            return

        print(f"Injecting: {new_text}")
        
        # Detect environment
        env = os.environ.copy()
        if 'WAYLAND_DISPLAY' not in env:
            uid = os.getuid()
            for i in range(2):
                path = f"/run/user/{uid}/wayland-{i}"
                if os.path.exists(path):
                    env['WAYLAND_DISPLAY'] = f"wayland-{i}"
                    break

        success = False
        
        # 1. Try Wayland (wl-copy) - Silent attempt
        if 'WAYLAND_DISPLAY' in env:
            try:
                process = subprocess.Popen(['wl-copy'], stdin=subprocess.PIPE, env=env, stderr=subprocess.DEVNULL)
                process.communicate(input=new_text.encode('utf-8'))
                if process.returncode == 0:
                    success = True
            except Exception:
                pass

        # 2. Try X11 / pyperclip (Silently fallback)
        if not success:
            try:
                pyperclip.copy(new_text)
                success = True
            except Exception:
                pass

        # 3. Final Fallback: Manual Typing
        if not success:
            print("Clipboard injection failed. Falling back to typing...")
            self.type_text(new_text)
            self.last_text = text
            return

        # Perform Paste (Ctrl+V)
        if self.ui:
            self.ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTCTRL, 1)
            self.ui.write(ecodes.EV_KEY, ecodes.KEY_V, 1)
            self.ui.write(ecodes.EV_KEY, ecodes.KEY_V, 0)
            self.ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTCTRL, 0)
            self.ui.syn()
        
        self.last_text = text

    def type_text(self, text):
        if not self.ui:
            return
        
        for char in text:
            key = None
            shift = False
            
            if char == " ": key = ecodes.KEY_SPACE
            elif char == ".": key = ecodes.KEY_DOT
            elif char == ",": key = ecodes.KEY_COMMA
            elif 'a' <= char <= 'z':
                key = getattr(ecodes, f"KEY_{char.upper()}")
            elif 'A' <= char <= 'Z':
                key = getattr(ecodes, f"KEY_{char}")
                shift = True
            elif '0' <= char <= '9':
                key = getattr(ecodes, f"KEY_{char}")
            
            if key:
                if shift: self.ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 1)
                self.ui.write(ecodes.EV_KEY, key, 1)
                self.ui.write(ecodes.EV_KEY, key, 0)
                if shift: self.ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 0)
                self.ui.syn()
                time.sleep(0.01)

    def run(self):
        self.setup_uinput()
        while self.running:
            try:
                text = self.text_queue.get(timeout=0.1)
                self.inject_text(text)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in text injection: {e}")

    def stop(self):
        self.running = False
        if self.ui:
            self.ui.close()
