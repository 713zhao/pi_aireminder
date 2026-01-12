"""
Run application with dummy events for testing
"""
import sys
import yaml
from datetime import datetime, timedelta

sys.path.insert(0, 'src')

from event_fetcher import Event
from display_manager import DisplayManager
from alarm_system import AlarmSystem
from main import ReminderSystem

# Monkey patch the fetch method to return dummy events
def create_dummy_events():
    now = datetime.now()
    return [
        Event('1', 'Morning Standup', 'Daily team meeting', now + timedelta(minutes=2)),
        Event('2', 'Coffee Break', 'Time for coffee and snacks', now + timedelta(minutes=5)),
        Event('3', 'Project Review', 'Review Q1 project status', now + timedelta(hours=1)),
        Event('4', 'Lunch Meeting', 'Lunch with the client', now + timedelta(hours=2)),
        Event('5', 'Code Review', 'Review pull requests', now + timedelta(hours=3)),
        Event('6', 'Team Training', 'New framework training session', now + timedelta(hours=4)),
    ]

# Override the fetch method
def patched_fetch_today_events(self):
    print("📋 Using dummy events for testing...")
    return create_dummy_events()

# Apply the patch
from event_fetcher import EventFetcher
EventFetcher.fetch_today_events = patched_fetch_today_events

# Now run the application
print("=" * 60)
print("AI Reminder System - Running with Dummy Events")
print("=" * 60)
print("\n✨ Features enabled:")
print("  - 6 dummy events loaded")
print("  - Voice reminders every 5 minutes (configurable)")
print("  - GUI with event display")
print("  - Status updates and colors")
print("\n⚠️  Note: Voice recognition and chatbot require additional setup")
print("=" * 60)
print()

system = ReminderSystem('config.yaml')
system.start()
