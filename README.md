# AI Reminder System - Setup Guide

## Quick Start

### 1. Run Setup Script
```bash
python setup.py
```

This will:
- Create necessary directories (logs, assets, models, src)
- Generate a sample alarm sound
- Check for installed dependencies

### 2. Install System Dependencies
```bash
# Install required system packages
sudo apt-get update
sudo apt-get install -y portaudio19-dev python3-pyaudio espeak espeak-ng
```

### 3. Install Python Dependencies
```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Download Vosk Model (for offline speech recognition)
```bash
# Download and extract the model
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip -d models/

# Or use a larger model for better accuracy:
# wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
```

### 5. Configure the System

Edit `config.yaml`:

```yaml
# Backend API - Update with your server URL
backend:
  url: "http://your-server.com/api"
  
# Add your API keys
chatbot:
  provider: "openai"  # or "gemini"
  openai:
    api_key: "sk-your-actual-api-key"
```

### 6. Test Audio Devices

```bash
# List audio devices
python -c "import pyaudio; p = pyaudio.PyAudio(); [print(f'{i}: {p.get_device_info_by_index(i)[\"name\"]}') for i in range(p.get_device_count())]"

# Test microphone
python -c "import speech_recognition as sr; r = sr.Recognizer(); m = sr.Microphone(); print('Speak now...'); print(r.recognize_google(r.listen(m)))"

# Test speaker/TTS
python -c "import pyttsx3; engine = pyttsx3.init(); engine.say('Testing audio'); engine.runAndWait()"
```

### 7. Run the Application

```bash
python src/main.py
```

---

## System Service (Auto-start on Boot)

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/pibot-reminder.service
```

Add the following content:

```ini
[Unit]
Description=AI Reminder System
After=network.target sound.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/PiBot
Environment="DISPLAY=:0"
Environment="XAUTHORITY=/home/pi/.Xauthority"
ExecStart=/home/pi/PiBot/venv/bin/python /home/pi/PiBot/src/main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable pibot-reminder.service
sudo systemctl start pibot-reminder.service

# Check status
sudo systemctl status pibot-reminder.service

# View logs
sudo journalctl -u pibot-reminder.service -f
```

---

## Troubleshooting

### Audio Issues

**No sound output:**
```bash
# Check ALSA
aplay -l

# Test speaker
speaker-test -t wav -c 2

# Set default audio device
sudo raspi-config
# Navigate to: System Options > Audio
```

**Microphone not working:**
```bash
# Record test
arecord -d 5 -f cd test.wav
aplay test.wav

# Adjust microphone volume
alsamixer
# Press F4 for capture, adjust with arrow keys
```

### Vosk Issues

**Model not found:**
- Ensure the model is extracted to the correct path
- Check `config.yaml` has the correct `model_path`
- Path should be: `models/vosk-model-small-en-us-0.15`

### Display Issues

**GUI not showing:**
```bash
# Check X display
echo $DISPLAY  # Should show :0 or :1

# Allow X access
xhost +local:

# Run with display
DISPLAY=:0 python src/main.py
```

**Wrong resolution:**
- Edit `config.yaml` and adjust `display.width` and `display.height`
- Or set `display.fullscreen: true`

### API Connection Issues

**Cannot fetch events:**
- Check `backend.url` in `config.yaml`
- Test with: `curl http://your-server.com/api/events/today`
- Check network connectivity
- Review logs in `logs/pibot.log`

**Chatbot not responding:**
- Verify API key is correct in `config.yaml`
- Check internet connection
- Test API key with curl:
  ```bash
  curl https://api.openai.com/v1/models \
    -H "Authorization: Bearer YOUR_API_KEY"
  ```

---

## Development & Testing

### Test Individual Components

**Test Event Fetcher:**
```python
python -c "
from src.event_fetcher import EventFetcher
import yaml
config = yaml.safe_load(open('config.yaml'))
fetcher = EventFetcher(config)
events = fetcher.fetch_today_events()
print(f'Found {len(events)} events')
for e in events: print(e)
"
```

**Test Alarm System:**
```python
python -c "
from src.alarm_system import AlarmSystem
import yaml
config = yaml.safe_load(open('config.yaml'))
alarm = AlarmSystem(config)
alarm.test_alarm()
"
```

**Test Voice Recognition:**
```python
python -c "
from src.voice_recognition import VoiceRecognition
import yaml
config = yaml.safe_load(open('config.yaml'))
vr = VoiceRecognition(config)
print('Speak something...')
text = vr.recognize_once()
print(f'Recognized: {text}')
"
```

---

## Hardware Optimization

### Reduce CPU Usage
- Use smaller Vosk model (`vosk-model-small-en-us-0.15`)
- Decrease `display.refresh_interval` in config
- Use lite model for Whisper if using API

### Improve Performance
- Overclock Raspberry Pi (use `sudo raspi-config`)
- Add heatsink/fan for thermal management
- Use faster SD card (Class 10 or UHS-I)

### Power Management
```bash
# Disable WiFi power management
sudo iw dev wlan0 set power_save off

# Disable screen blanking
sudo nano /etc/xdg/lxsession/LXDE-pi/autostart
# Add: @xset s off
#      @xset -dpms
#      @xset s noblank
```

---

## Backup & Restore

### Backup Configuration
```bash
tar -czf pibot-backup-$(date +%Y%m%d).tar.gz \
  config.yaml \
  assets/ \
  logs/ \
  src/
```

### Restore
```bash
tar -xzf pibot-backup-YYYYMMDD.tar.gz
```

---

## Security Notes

1. **API Keys**: Never commit `config.yaml` with real API keys to version control
2. **Network**: Use HTTPS for backend communication
3. **Firewall**: Configure firewall if exposing any ports
4. **Updates**: Keep system and dependencies updated
   ```bash
   sudo apt update && sudo apt upgrade
   pip install --upgrade -r requirements.txt
   ```

---

## Support

For issues or questions:
1. Check logs in `logs/pibot.log`
2. Review configuration in `config.yaml`
3. Test individual components
4. Check system resources: `htop`

---

## License

This project is provided as-is for educational and personal use.
