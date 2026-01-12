"""
Run application with Google Calendar integration
"""
import sys
sys.path.insert(0, 'src')

try:
    from google_calendar_fetcher import GoogleCalendarFetcher, GOOGLE_AVAILABLE
    from main import ReminderSystem
    from event_fetcher import EventFetcher
    
    if not GOOGLE_AVAILABLE:
        print("❌ Google Calendar libraries not installed!")
        print("\nInstall with:")
        print("  pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        sys.exit(1)
    
    # Override the fetch method to use Google Calendar
    original_fetch = EventFetcher.fetch_today_events
    
    def patched_fetch_today_events(self):
        print("📅 Fetching events from Google Calendar...")
        try:
            fetcher = GoogleCalendarFetcher()
            if fetcher.service:
                return fetcher.fetch_today_events()
            else:
                print("⚠️  Google Calendar not available, using backend...")
                return original_fetch(self)
        except Exception as e:
            print(f"⚠️  Google Calendar error: {e}")
            print("   Falling back to backend...")
            return original_fetch(self)
    
    EventFetcher.fetch_today_events = patched_fetch_today_events
    
    print("=" * 60)
    print("AI Reminder System - Google Calendar Integration")
    print("=" * 60)
    print("\n✨ Features:")
    print("  - Fetches events from your Google Calendar")
    print("  - Auto-syncs every 60 seconds")
    print("  - Voice reminders at event time")
    print("  - GUI with live updates")
    print("\n🔐 First run will open browser for authentication")
    print("=" * 60)
    print()
    
    # Run the application
    system = ReminderSystem('config.yaml')
    system.start()
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nMake sure you have installed:")
    print("  pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)
