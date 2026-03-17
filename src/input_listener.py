import evdev
from evdev import ecodes
import threading
import time
import os

class InputListener(threading.Thread):
    def __init__(self, config, on_press, on_release):
        super().__init__(daemon=True)
        self.config = config
        self.on_press = on_press
        self.on_release = on_release
        self.device = None
        self.target_keys = set()
        self.hotkey_names = []
        self.pressed_keys = set()
        self.running = True

    def find_device(self):
        saved_path = self.config.get("evdev_device")
        if saved_path and os.path.exists(saved_path):
            return evdev.InputDevice(saved_path)
        
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        for dev in devices:
            # Look for devices with KEY capability and that are likely keyboards
            if ecodes.EV_KEY in dev.capabilities():
                capabilities = dev.capabilities()[ecodes.EV_KEY]
                if ecodes.KEY_A in capabilities: # Generic check for keyboard
                    print(f"Automatically selected input device: {dev.name} ({dev.path})")
                    return dev
        return None

    def update_hotkey(self):
        self.hotkey_names = self.config.get("hotkey", ["KEY_LEFTMETA", "KEY_SPACE"])
        print(f"Updating hotkey to: {self.hotkey_names}")
        self.target_keys = {ecodes.ecodes[name] for name in self.hotkey_names}
        self.pressed_keys.clear()

    def update_device(self):
        print("Triggering input device re-selection...")
        # Since read_loop is blocking in another thread, we'll just let find_device
        # pick the new one on the next iteration if the current one is disconnected
        # OR we can force a restart of the loop by setting device to None if they differ.
        if self.device and self.device.path != self.config.get("evdev_device"):
            # This is tricky because read_loop blocks. 
            # For now, we'll recommend a restart or try to close it.
            try:
                self.device.close()
            except:
                pass
            self.device = None

    def run(self):
        self.update_hotkey()
        
        while self.running:
            try:
                self.device = self.find_device()
                if not self.device:
                    print("No suitable input device found. Retrying in 5s...")
                    time.sleep(5)
                    continue

                if self.device:
                    print(f"[*] Listening on {self.device.path} for {self.hotkey_names}")
                
                if self.device:
                    active = False
                    for event in self.device.read_loop():
                        if not self.running:
                            break
                        
                        if event.type == ecodes.EV_KEY:
                            key_event = evdev.categorize(event)
                            scancode = key_event.scancode
                            
                            if key_event.keystate == evdev.KeyEvent.key_down:
                                self.pressed_keys.add(scancode)
                            elif key_event.keystate == evdev.KeyEvent.key_up:
                                if scancode in self.pressed_keys:
                                    self.pressed_keys.discard(scancode)
                            
                            is_match = self.target_keys.issubset(self.pressed_keys)
                            if is_match and not active:
                                active = True
                                self.on_press()
                            elif not is_match and active:
                                active = False
                                self.on_release()
            except Exception as e:
                print(f"Error in input listener: {e}")
                time.sleep(1)

    def stop(self):
        self.running = False
