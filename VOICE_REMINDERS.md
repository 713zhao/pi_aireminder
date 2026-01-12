# Voice Reminder Configuration Guide

## Overview

The system now uses **voice-only reminders** - no beep sounds. Voice announcements repeat at configurable intervals until stopped by user.

## Configuration

Edit `config.yaml`:

```yaml
alarm:
  voice_reminder_interval: 300  # Seconds between voice reminders (default: 5 minutes)
  auto_stop_after: 1800         # Auto-stop after 30 minutes if not acknowledged
```

### Common Intervals

| Minutes | Seconds | Use Case |
|---------|---------|----------|
| 1       | 60      | Testing / Very urgent |
| 3       | 180     | Urgent reminders |
| 5       | 300     | **Default - Normal reminders** |
| 10      | 600     | Less intrusive |
| 15      | 900     | Minimal interruption |

## How It Works

### Initial Trigger
When an event time arrives:
1. ✅ Voice announces: "Reminder: [Event Title]"
2. ✅ Voice reads description (if available)
3. ✅ Display shows orange "IN PROGRESS" status
4. ⏱️ Timer starts for next reminder

### Repeat Cycle
Every `voice_reminder_interval` seconds:
1. ✅ Voice repeats: "Reminder: [Event Title]"
2. ✅ Voice reads description again
3. ⏱️ Continues until stopped or timeout

### Auto-Stop
After `auto_stop_after` seconds (default 30 minutes):
- Reminder automatically stops
- No more voice announcements
- Display updates to "EXPIRED" status

## Stop Methods

### 1. Voice Command ✅
Say: **"stop"** or **"assistant stop"**
- Requires voice recognition enabled
- Works from anywhere
- Instant stop

### 2. HMI Screen Button ✅
Click the red **STOP** button on screen:
- Visual confirmation
- Works without voice recognition
- Touch-friendly for Raspberry Pi touchscreen

### 3. Keyboard (Development) ✅
Press the STOP button in test GUI:
- For development/testing
- Same as HMI button

## Testing

### Test 1: Voice Only (Console)
```bash
python test_voice_only.py
```
- Tests voice reminders without GUI
- Shows timing and intervals
- Press Ctrl+C to stop

### Test 2: GUI with Stop Button
```bash
python test_stop_button.py
```
- Full GUI with visual stop button
- Shows event in "IN PROGRESS" status
- Click STOP button to silence

### Test 3: Quick Test (30 seconds)
Modify for testing:
```yaml
alarm:
  voice_reminder_interval: 30  # 30 seconds instead of 5 minutes
  auto_stop_after: 120         # 2 minutes instead of 30
```

## Voice Announcement Format

### First Announcement
```
"Reminder: [Event Title]"
[pause]
"[Event Description]"
```

### Repeat Announcements
```
"Reminder: [Event Title]"
[pause]
"[Event Description]"
```

## Customization

### Change Voice Speed
Edit `config.yaml`:
```yaml
tts:
  rate: 150      # Words per minute (default)
  # Try: 120 (slower), 180 (faster)
```

### Change Voice Volume
```yaml
tts:
  volume: 0.9    # 0.0 to 1.0
```

### Change Voice (Windows)
```python
# In alarm_system.py, list available voices:
import pyttsx3
engine = pyttsx3.init()
for voice in engine.getProperty('voices'):
    print(voice.id, voice.name)
```

Then set in `config.yaml`:
```yaml
tts:
  voice: "HKEY_LOCAL_MACHINE\\SOFTWARE\\..."  # Voice ID from above
```

## Display Integration

### Status During Reminder
- **Background**: Orange (#f39c12)
- **Status**: ▶ IN PROGRESS
- **Border**: Orange highlight
- **Text**: "Reminder active - Click STOP to silence"

### After Stopping
- **Background**: Dark
- **Status**: ✓ COMPLETED (if manually stopped)
- **Border**: Green
- **Text**: Returns to normal

## Performance

### CPU Usage
- Voice synthesis: Low (pyttsx3 is offline)
- Repeat checking: Minimal (10-second intervals)
- Total overhead: < 5% on Raspberry Pi 4

### Memory
- TTS engine: ~20MB
- Audio buffers: ~5MB
- Total: ~25MB additional

## Best Practices

### For Work Environment
```yaml
voice_reminder_interval: 300   # 5 minutes
auto_stop_after: 1800          # 30 minutes
tts:
  volume: 0.7                  # Moderate volume
```

### For Personal Use
```yaml
voice_reminder_interval: 180   # 3 minutes
auto_stop_after: 900           # 15 minutes
tts:
  volume: 0.9                  # Higher volume
```

### For Overnight/Background
```yaml
voice_reminder_interval: 600   # 10 minutes
auto_stop_after: 3600          # 1 hour
tts:
  volume: 0.5                  # Lower volume
```

## Troubleshooting

### Voice Not Playing
1. Check TTS engine initialized:
   ```bash
   python -c "import pyttsx3; e=pyttsx3.init(); e.say('test'); e.runAndWait()"
   ```
2. Check system audio output
3. Verify `tts.volume` > 0 in config

### Voice Too Fast/Slow
Adjust `tts.rate` in config.yaml:
- Default: 150 words/minute
- Range: 50-300 (reasonable)

### Voice Stopping Too Soon
Check `auto_stop_after` value:
- Should be in seconds (not minutes)
- Default 1800 = 30 minutes

### Voice Not Repeating
Verify `voice_reminder_interval`:
- Should be > 0
- Logs show: "Next reminder in X seconds"
- Check logs/pibot.log for errors

## Example Scenarios

### Scenario 1: Meeting Reminder
```
Event: "Team Standup"
Description: "Daily sync at 9 AM"

9:00 AM - "Reminder: Team Standup. Daily sync at 9 AM"
9:05 AM - "Reminder: Team Standup. Daily sync at 9 AM"
9:10 AM - "Reminder: Team Standup. Daily sync at 9 AM"
[User says "stop" or clicks STOP button]
✅ Stopped
```

### Scenario 2: Break Reminder
```
Event: "Take a Break"
Description: "Stand up and stretch"

3:00 PM - "Reminder: Take a Break. Stand up and stretch"
3:05 PM - "Reminder: Take a Break. Stand up and stretch"
[User completes break, clicks STOP]
✅ Marked complete
```

### Scenario 3: Auto-Stop
```
Event: "Optional Meeting"
Description: "Join if available"

2:00 PM - "Reminder: Optional Meeting. Join if available"
2:05 PM - [repeat]
2:10 PM - [repeat]
...
2:30 PM - Auto-stopped (30 minutes elapsed)
Status: EXPIRED
```

## Integration with Main Application

In `src/main.py`, the system automatically:
1. ✅ Checks events every 10 seconds
2. ✅ Triggers voice reminders when event time arrives
3. ✅ Manages repeat intervals
4. ✅ Listens for "stop" voice command
5. ✅ Shows stop button on GUI
6. ✅ Updates display status

No additional configuration needed - just adjust intervals in `config.yaml`.

## Files Modified

- `src/alarm_system.py` - Removed beep sound playback
- `config.yaml` - Documented voice reminder settings
- `test_voice_only.py` - New test for voice-only mode
- `test_stop_button.py` - Existing test with stop button

## Summary

✅ **Voice reminders only** - no beep sounds  
✅ **Configurable interval** - default 5 minutes  
✅ **Auto-stop** - default 30 minutes  
✅ **Multiple stop methods** - voice, GUI button, keyboard  
✅ **Visual status** - IN PROGRESS display  
✅ **Tested and working** - ready for Raspberry Pi deployment
