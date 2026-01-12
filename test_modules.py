"""
Test script for individual modules
"""
import sys
import yaml
from datetime import datetime, timedelta

sys.path.insert(0, 'src')

from event_fetcher import Event
from alarm_system import AlarmSystem

def test_event_creation():
    """Test Event creation"""
    print("\n=== Testing Event Creation ===")
    now = datetime.now()
    event = Event(
        id='test-1',
        title='Test Reminder',
        description='This is a test event',
        event_time=now + timedelta(minutes=5)
    )
    print(f"✓ Created event: {event}")
    print(f"  Time: {event.event_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Triggered: {event.triggered}")
    return event

def test_alarm_system(event):
    """Test Alarm System"""
    print("\n=== Testing Alarm System ===")
    config = yaml.safe_load(open('config.yaml'))
    alarm = AlarmSystem(config)
    
    print("✓ Alarm system initialized")
    print(f"  Alarm sound loaded: {alarm.alarm_sound is not None}")
    print(f"  TTS engine ready: {alarm.tts_engine is not None}")
    
    # Test TTS
    print("\n  Testing Text-to-Speech...")
    alarm._speak("Testing alarm system")
    print("✓ TTS test complete")
    
    # Test alarm sound (brief play)
    if alarm.alarm_sound:
        print("\n  Testing alarm sound...")
        alarm.alarm_sound.play()
        import time
        time.sleep(1)
        alarm.stop_alarm()
        print("✓ Alarm sound test complete")
    
    alarm.cleanup()
    return True

def test_config():
    """Test configuration loading"""
    print("\n=== Testing Configuration ===")
    config = yaml.safe_load(open('config.yaml'))
    
    print("✓ Config loaded successfully")
    print(f"  Backend URL: {config['backend']['url']}")
    print(f"  Display size: {config['display']['width']}x{config['display']['height']}")
    print(f"  Speech engine: {config['speech']['engine']}")
    print(f"  Chatbot provider: {config['chatbot']['provider']}")
    return config

def main():
    print("=" * 60)
    print("AI Reminder System - Module Tests")
    print("=" * 60)
    
    try:
        # Test configuration
        config = test_config()
        
        # Test event creation
        event = test_event_creation()
        
        # Test alarm system
        test_alarm_system(event)
        
        print("\n" + "=" * 60)
        print("✓ All module tests passed!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Configure your backend URL in config.yaml")
        print("2. Add API keys for OpenAI/Gemini if using chatbot")
        print("3. Download Vosk model for voice recognition")
        print("4. Run: python src/main.py")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
