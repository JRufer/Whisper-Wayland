# Whisper Wayland

Whisper Wayland is a native, on-device voice-to-text (dictation) tool designed for Linux, with first-class support for Wayland (and X11 compatibility). It uses OpenAI's Whisper model (via `faster-whisper`) and Silero VAD to provide fast, accurate, and private transcription that injects text directly into your active window.

![Record On](assets/record_on.png)

## Features

- **On-Device AI**: All transcription happens locally on your machine. No keys or data leave your computer.
- **Global Hotkey**: Trigger recording with a configurable system-wide shortcut (default: `Super+Space`).
- **Wayland Compatible**: Uses `evdev` for global input and `uinput` for text injection, bypassing Wayland's security restrictions on traditional key-loggers and injectors.
- **Premium UI**: Sleek system tray icon with distinct "record button" states.
- **Settings GUI**: Easy-to-use interface to change models, select audio devices, record new hotkeys, and adjust microphone boost.
- **Microphone Boost**: In-app software gain control for quiet microphones.
- **Automatic Fallback**: Gracefully falls back to CPU if no NVIDIA GPU/CUDA is detected.

## Installation

### Prerequisites

You will need `portaudio`, `python`, and `python-pip`.

On Arch Linux:
```bash
sudo pacman -S portaudio python-pip wl-clipboard
```

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/jrufer/whisper-wayland.git
   cd whisper-wayland
   ```

2. **Create a virtual environment and install dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Udev Rules (Required for Hotkeys/Injection)**:
   For the app to listen to your keyboard and inject text without root privileges, you need to add your user to the `input` and `uinput` groups and set up udev rules.
   
   Create `/etc/udev/rules.d/99-whisper-wayland.rules`:
   ```bash
   KERNEL=="uinput", GROUP="uinput", MODE="0660"
   ```
   Then reload rules and add yourself to the groups:
   ```bash
   sudo udevadm control --reload-rules && sudo udevadm trigger
   sudo usermod -aG input,uinput $USER
   ```
   *Note: You may need to log out and back in for group changes to take effect.*

## Usage

### Launching

- **From Terminal**:
  ```bash
  source venv/bin/activate
  python src/main.py
  ```
- **From GUI**:
  The project includes a `.desktop` file. On first run via terminal, it installs a shortcut to your applications menu. You can then search for "Whisper Wayland" in your launcher.

### How to Dictate

1.  **Hold** the hotkey (default: `Super+Space`).
2.  The tray icon will turn **red**, indicating it is recording.
3.  **Speak** clearly.
4.  **Release** the hotkey.
5.  The app will transcribe your speech and automatically **paste/type** it into your active window.

## Configuration

Access **Settings** by right-clicking the tray icon.

- **Model Selection**: Choose between `tiny`, `base`, `small`, etc. (Larger is more accurate but slower).
- **Audio Device**: Select which microphone to use.
- **Mic Boost**: Increase sensitivity if the AI isn't picking up your voice.
- **Hotkey**: Click "Record" and press your desired combination to change the trigger.

## License

MIT
