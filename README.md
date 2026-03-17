# Whisper Wayland

Whisper Wayland is a native, on-device voice-to-text (dictation) tool designed for Linux, with first-class support for Wayland (and X11 compatibility). It uses OpenAI's Whisper model (via `faster-whisper`) and Silero VAD to provide fast, accurate, and private transcription that injects text directly into your active window.

![Record On](assets/record_on.png)

## Features

- **Near Real-Time Transcription**: See what the AI hears *as you speak* via a floating overlay at the bottom of your screen.
- **Hands-Free Mode**: Toggle recording on/off with a separate hotkey (instead of holding).
- **GPU & CPU Support**: Manually select between CPU and CUDA (GPU) in settings with automatic optimization (e.g., `int8` for CPU, `float16` for GPU).
- **Auto-Optimized CUDA**: Automated discovery of CUDA/cuDNN libraries even in restricted Python environments.

## Installation

You will need `portaudio`, `python`, and `python-pip`.

On Arch Linux:
```bash
sudo pacman -S portaudio python-pyaudio wl-clipboard
```

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/jrufer/whisper-wayland.git
   cd whisper-wayland
   ```

2. **Install dependencies**:
   For the best experience (including GPU support), we recommend using the binary versions of `ctranslate2`:
   ```bash
   # Install core dependencies
   pip install --user --break-system-packages -r requirements.txt
   
   # Optional: For NVIDIA GPU Acceleration (Highly Recommended)
   pip install --user --break-system-packages nvidia-cublas-cu12 nvidia-cudnn-cu12
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

There are two ways to record:

- **Hold to Talk**: Hold the "Hold" hotkey (default: `Super+Space`), speak, and release.
- **Toggle to Talk**: Tap the "Toggle" hotkey (default: `Ctrl+Super+Space`) to start, and tap again to stop.

While recording:
- The tray icon turns **red**.
- A **floating overlay** appears at the bottom of the screen showing real-time feedback.
- Upon stopping, the final text is automatically **typed** into your active window.

## Configuration & Features

![Settings Window](assets/settings.png)

The settings window allows you to fine-tune the dictation experience to match your hardware and preferences.

### 1. Whisper Model
Choose the AI model size that fits your system's performance:
- **Tiny/Base**: Extremely fast, low resource usage, good for clear speech.
- **Small/Medium**: Better accuracy, especially for accents or noisy environments.
- **Large-v3**: Highest accuracy, requires more VRAM/compute power.

### 2. Audio Input Device
Select your primary microphone from the list of detected system devices. The app supports a wide range of hardware, including USB headsets and professional interfaces.

### 4. GPU/CPU Device Selection
Manually select which hardware to use. `CUDA` is recommended for speed. The app automatically applies optimal compute types (`float16` for GPU, `int8` for CPU) to maximize performance.

### 5. Hotkeys (Hold & Toggle)
Configurable triggers for both recording styles. The "Hold" hotkey is great for quick bursts, while "Toggle" is perfect for long-form dictation.

### 6. Real-Time Overlay
A toggle to enable or disable the floating feedback window.

### 7. Microphone Boost (Software Gain)
If the AI isn't picking up your voice at normal volumes, use the **Software Gain** slider to digitally amplify the signal (up to 5.0x).

## License

MIT
