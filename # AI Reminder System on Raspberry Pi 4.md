# AI Reminder System on Raspberry Pi 4

## Overview
This project turns a Raspberry Pi 4 into a smart reminder and voice assistant device.

The system:
- Fetches today's events from a web backend (AIreminder)
- Displays events on a Pi-connected screen
- Triggers alarms at event time (sound + TTS)
- Allows voice command **"stop"** to stop alarms immediately
- Supports a voice chatbot using LLMs (OpenAI or Gemini)
- Uses offline speech recognition (Vosk) and optional online Whisper
- Is implemented using Object-Oriented Python design

---

## Recommended Raspberry Pi OS

### ✅ Best choice (recommended)
**Raspberry Pi OS (64-bit) with Desktop – Bookworm**

Reasons:
- Best display + audio driver support
- Tkinter GUI works out of the box
- USB mic and speaker work reliably
- Easier debugging and maintenance

### ⚠️ Alternative (advanced users)
**Raspberry Pi OS Lite (64-bit)**  
Requires manual setup of:
- X11 / window manager
- Fonts
- Audio routing

---

## Hardware Requirements
- Raspberry Pi 4 (2GB minimum, 4GB+ recommended)
- HDMI / DSI display
- USB microphone (recommended over analog mic)
- Speaker (USB / 3.5mm / HDMI)
- Internet connection (Wi-Fi or Ethernet)

Optional:
- Physical STOP button (GPIO fallback)
- Camera (future extension)

---

## System Packages (Install Once)

```bash
sudo apt update
sudo apt install -y \
  python3 \
  python3-pip \
  python3-venv \
  python3-tk \
  portaudio19-dev \
  libatlas-base-dev \
  alsa-utils \
  git
