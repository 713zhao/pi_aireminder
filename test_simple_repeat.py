"""
Simple test for voice reminder repeat
"""
import sys
sys.path.insert(0, 'src')

import yaml
import time
from datetime import datetime
from alarm_system import AlarmSystem
from event_fetcher import Event

# Load config with short interval
config = yaml.safe_load(open('config.yaml'))
config['alarm']['voice_reminder_interval'] = 15  # 15 seconds
config['alarm']['auto_stop_after'] = 60  # 1 minute

print("Testing voice reminder repeat every 15 seconds...")
print("Will run for 45 seconds, should hear 3 reminders\n")

# Create alarm
alarm = AlarmSystem(config)

# Create event
event = Event('1', 'Test Reminder', 'This should repeat', datetime.now())

# Trigger
alarm.trigger_alarm(event)

# Wait and observe
try:
    time.sleep(45)
except KeyboardInterrupt:
    pass

# Stop
print("\nStopping...")
alarm.stop_alarm()
alarm.cleanup()
print("Done!")
