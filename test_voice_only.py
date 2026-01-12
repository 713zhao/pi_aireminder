"""
Test Voice Reminders - No Beep Sound
Demonstrates voice reminders repeating every 5 minutes (configurable)
"""
import sys
import yaml
from datetime import datetime, timedelta
import time

sys.path.insert(0, 'src')

from event_fetcher import Event
from alarm_system import AlarmSystem

def main():
    print("=" * 60)
    print("Voice Reminder Test - No Beep Sound")
    print("=" * 60)
    
    # Load config
    config = yaml.safe_load(open('config.yaml'))
    
    # Show settings
    voice_interval = config['alarm']['voice_reminder_interval']
    auto_stop = config['alarm']['auto_stop_after']
    
    print(f"\nSettings:")
    print(f"  Voice reminder interval: {voice_interval} seconds ({voice_interval//60} minutes)")
    print(f"  Auto-stop after: {auto_stop} seconds ({auto_stop//60} minutes)")
    print(f"\n✨ Only voice reminders - NO beep sounds")
    print(f"\nFor testing, we'll use 30 seconds instead of 5 minutes...")
    
    # Temporarily change interval for testing
    config['alarm']['voice_reminder_interval'] = 30  # 30 seconds for demo
    config['alarm']['auto_stop_after'] = 120  # 2 minutes for demo
    
    # Create alarm system
    alarm = AlarmSystem(config)
    
    # Create test event
    now = datetime.now()
    event = Event(
        id='test-1',
        title='Team Meeting',
        description='Weekly sync with the development team',
        event_time=now
    )
    
    print(f"\n🔔 Triggering reminder for: {event.title}")
    print(f"   Description: {event.description}")
    print(f"\nVoice will repeat every 30 seconds...")
    print("Press Ctrl+C to stop\n")
    print("-" * 60)
    
    try:
        # Trigger the reminder
        alarm.trigger_alarm(event)
        
        # Let it run and show status
        start = time.time()
        while alarm.is_playing:
            elapsed = int(time.time() - start)
            print(f"\r⏱️  Running: {elapsed}s | Next voice in: {30 - (elapsed % 30)}s", end='', flush=True)
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping reminder...")
        alarm.stop_alarm()
        print("✅ Reminder stopped")
    
    finally:
        alarm.cleanup()
        print("\n" + "=" * 60)
        print("Test completed!")
        print("\nTo change voice reminder interval:")
        print("  Edit config.yaml -> alarm -> voice_reminder_interval")
        print("  Default: 300 seconds (5 minutes)")
        print("=" * 60)

if __name__ == "__main__":
    main()
