"""
GUI Test - Display test events
"""
import sys
import yaml
from datetime import datetime, timedelta

sys.path.insert(0, 'src')

from event_fetcher import Event
from display_manager import DisplayManager

def main():
    print("Starting GUI test...")
    print("Close the window to exit")
    
    # Load config
    config = yaml.safe_load(open('config.yaml'))
    
    # Create display
    display = DisplayManager(config)
    
    # Create sample events
    now = datetime.now()
    events = [
        Event('1', 'Morning Standup', 'Daily team sync meeting', now + timedelta(hours=2)),
        Event('2', 'Current Meeting', 'This meeting is happening now!', now - timedelta(minutes=15)),
        Event('3', 'Lunch Break', 'Time to eat', now + timedelta(hours=4)),
        Event('4', 'Urgent Call', 'Starting in 3 minutes!', now + timedelta(minutes=3)),
        Event('5', 'Yesterday Meeting', 'This was yesterday', now - timedelta(hours=25)),
        Event('6', 'Completed Task', 'This was done', now - timedelta(hours=2), triggered=True),
        Event('7', 'Expired Event', 'This expired 2 hours ago', now - timedelta(hours=2)),
        Event('8', 'Afternoon Workshop', 'Training session', now + timedelta(hours=6)),
    ]
    
    # Update display with events
    display.update_events(events)
    
    # Show status
    display.update_status("🟢 GUI Test Mode - All Systems Ready", "#4ecca3")
    
    # Run GUI
    display.run()

if __name__ == "__main__":
    main()
