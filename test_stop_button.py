"""
GUI Test with Stop Button
Tests the HMI screen stop button functionality
"""
import sys
import yaml
import threading
import time
from datetime import datetime, timedelta

sys.path.insert(0, 'src')

from event_fetcher import Event
from display_manager import DisplayManager
from alarm_system import AlarmSystem

class StopButtonTest:
    def __init__(self):
        # Load config
        self.config = yaml.safe_load(open('config.yaml'))
        
        # Adjust intervals for testing
        self.config['alarm']['voice_reminder_interval'] = 15  # 15 seconds
        self.config['alarm']['repeat_interval'] = 5
        self.config['alarm']['auto_stop_after'] = 120  # 2 minutes
        
        # Create components
        self.display = DisplayManager(self.config)
        self.alarm = AlarmSystem(self.config)
        
        # Connect stop button to alarm
        self.display.set_stop_alarm_callback(self.on_stop_alarm)
        
        # Create test events
        now = datetime.now()
        self.events = [
            Event('1', 'Test Alarm Event', 'Click STOP ALARM button to stop', now),
            Event('2', 'Future Event', 'This is upcoming', now + timedelta(hours=2)),
        ]
        
        self.alarm_triggered = False
        
    def on_stop_alarm(self):
        """Called when stop button is clicked"""
        print("\n✓ STOP button clicked!")
        self.alarm.stop_alarm()
        self.display.clear_alarm()
        self.display.update_status("✓ Alarm stopped by user", "#4ecca3")
        
    def trigger_test_alarm(self):
        """Trigger alarm after a delay"""
        time.sleep(2)
        
        if not self.alarm_triggered:
            print("\n⏰ Triggering test alarm...")
            print("Click the STOP ALARM button to stop")
            print("Or say 'stop' if voice recognition is enabled\n")
            
            self.alarm_triggered = True
            event = self.events[0]
            
            self.display.show_alarm(event)
            self.alarm.trigger_alarm(event)
    
    def run(self):
        print("=" * 60)
        print("GUI Stop Button Test")
        print("=" * 60)
        print("\nConfiguration:")
        print(f"  Voice reminder every: {self.config['alarm']['voice_reminder_interval']}s")
        print(f"  Sound repeat every: {self.config['alarm']['repeat_interval']}s")
        print(f"  Auto-stop after: {self.config['alarm']['auto_stop_after']}s")
        print("\n✨ An alarm will trigger in 2 seconds")
        print("✨ Click the red 'STOP ALARM' button to stop it")
        print("=" * 60 + "\n")
        
        # Update display
        self.display.update_events(self.events)
        self.display.update_status("🟢 Waiting to trigger test alarm...", "#f39c12")
        
        # Start alarm trigger thread
        alarm_thread = threading.Thread(target=self.trigger_test_alarm, daemon=True)
        alarm_thread.start()
        
        # Run GUI
        self.display.run()

if __name__ == "__main__":
    test = StopButtonTest()
    test.run()
