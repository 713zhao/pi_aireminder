"""
Test Alarm System with Voice Reminders
Demonstrates:
- Initial voice announcement
- Periodic voice reminders every 5 minutes (configurable)
- Stop by GUI button
- Auto-stop after timeout
"""
import sys
import yaml
import time
from datetime import datetime

sys.path.insert(0, 'src')

from event_fetcher import Event
from alarm_system import AlarmSystem

def test_voice_reminders():
    print("=" * 60)
    print("Voice Reminder System Test")
    print("=" * 60)
    
    # Load config
    config = yaml.safe_load(open('config.yaml'))
    
    # Show configuration
    voice_interval = config['alarm']['voice_reminder_interval']
    sound_interval = config['alarm']['repeat_interval']
    auto_stop = config['alarm']['auto_stop_after']
    
    print(f"\nConfiguration:")
    print(f"  Voice Reminder Interval: {voice_interval}s ({voice_interval//60} minutes)")
    print(f"  Sound Repeat Interval: {sound_interval}s")
    print(f"  Auto Stop After: {auto_stop}s ({auto_stop//60} minutes)")
    
    # Create alarm system
    alarm = AlarmSystem(config)
    
    # Create test event
    event = Event(
        id='test-1',
        title='Important Meeting',
        description='Team sync with management',
        event_time=datetime.now()
    )
    
    print(f"\n✓ Alarm system initialized")
    print(f"✓ Test event created: {event.title}")
    
    # For testing, temporarily reduce intervals
    print("\n⚠ Adjusting intervals for testing:")
    print("  - Voice reminders every 10 seconds (instead of 5 minutes)")
    print("  - Sound repeats every 5 seconds")
    print("  - Auto-stop after 40 seconds (instead of 30 minutes)")
    
    alarm.alarm_config['voice_reminder_interval'] = 10  # 10 seconds for testing
    alarm.alarm_config['repeat_interval'] = 5
    alarm.alarm_config['auto_stop_after'] = 40
    
    print("\n" + "=" * 60)
    print("Starting alarm...")
    print("You should hear:")
    print("  1. Initial voice announcement")
    print("  2. Alarm sound every 5 seconds")
    print("  3. Voice reminder every 10 seconds")
    print("  4. Auto-stop after 40 seconds")
    print("\nPress Ctrl+C to stop manually")
    print("=" * 60 + "\n")
    
    try:
        # Trigger alarm
        alarm.trigger_alarm(event)
        
        # Monitor the alarm
        start = time.time()
        while alarm.is_playing:
            elapsed = int(time.time() - start)
            print(f"\r⏱ Elapsed: {elapsed}s | Status: {'ACTIVE' if alarm.is_playing else 'STOPPED'}", end='', flush=True)
            time.sleep(0.5)
        
        print("\n\n✓ Alarm stopped")
        print(f"✓ Total duration: {int(time.time() - start)} seconds")
        
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        alarm.stop_alarm()
    
    finally:
        alarm.cleanup()
        print("\n" + "=" * 60)
        print("Test complete")
        print("=" * 60)

if __name__ == "__main__":
    test_voice_reminders()
