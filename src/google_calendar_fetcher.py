"""
Google Calendar Integration
Fetches events from Google Calendar API
"""
import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from event_fetcher import Event

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False


class GoogleCalendarFetcher:
    """Fetches events from Google Calendar"""
    
    # Scopes required for reading calendar events
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    
    def __init__(self, credentials_file='credentials.json', token_file='token.json'):
        self.logger = logging.getLogger(__name__)
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        
        if not GOOGLE_AVAILABLE:
            self.logger.error("Google Calendar libraries not installed")
            self.logger.error("Run: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
            return
        
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Calendar API"""
        creds = None
        
        # Check if token file exists
        if os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
            except Exception as e:
                self.logger.error(f"Failed to load token: {e}")
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    self.logger.info("Refreshed Google Calendar credentials")
                except Exception as e:
                    self.logger.error(f"Failed to refresh credentials: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_file):
                    self.logger.error(f"Credentials file not found: {self.credentials_file}")
                    self.logger.error("Download credentials.json from Google Cloud Console")
                    return
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                    self.logger.info("Successfully authenticated with Google Calendar")
                except Exception as e:
                    self.logger.error(f"Authentication failed: {e}")
                    return
            
            # Save credentials for future use
            try:
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                self.logger.error(f"Failed to save token: {e}")
        
        # Build the service
        try:
            self.service = build('calendar', 'v3', credentials=creds)
            self.logger.info("Google Calendar service initialized")
        except Exception as e:
            self.logger.error(f"Failed to build calendar service: {e}")
    
    def fetch_today_events(self, calendar_id='primary') -> List[Event]:
        """Fetch today's events from Google Calendar"""
        if not self.service:
            self.logger.error("Calendar service not initialized")
            return []
        
        try:
            # Get start and end of today
            now = datetime.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            
            # Convert to RFC3339 format
            time_min = today_start.isoformat() + 'Z'
            time_max = today_end.isoformat() + 'Z'
            
            self.logger.info(f"Fetching events from {today_start} to {today_end}")
            
            # Call the Calendar API
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events_data = events_result.get('items', [])
            
            if not events_data:
                self.logger.info("No events found for today")
                return []
            
            events = []
            for item in events_data:
                event = self._parse_google_event(item)
                if event:
                    events.append(event)
            
            self.logger.info(f"Fetched {len(events)} events from Google Calendar")
            return events
            
        except Exception as e:
            self.logger.error(f"Failed to fetch events: {e}")
            return []
    
    def _parse_google_event(self, item: dict) -> Optional[Event]:
        """Parse a Google Calendar event into our Event object"""
        try:
            event_id = item['id']
            title = item.get('summary', 'Untitled Event')
            description = item.get('description', '')
            
            # Get event time
            start = item['start'].get('dateTime', item['start'].get('date'))
            
            # Parse the datetime
            if 'T' in start:
                # DateTime event
                event_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
            else:
                # All-day event - set to 9 AM
                event_time = datetime.fromisoformat(start + 'T09:00:00')
            
            # Convert to local time if needed
            if event_time.tzinfo:
                event_time = event_time.replace(tzinfo=None)
            
            return Event(
                id=event_id,
                title=title,
                description=description,
                event_time=event_time,
                triggered=False
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse event: {e}")
            return None
    
    def list_calendars(self):
        """List all available calendars"""
        if not self.service:
            self.logger.error("Calendar service not initialized")
            return []
        
        try:
            calendars_result = self.service.calendarList().list().execute()
            calendars = calendars_result.get('items', [])
            
            print("\n📅 Available Calendars:")
            print("=" * 60)
            for calendar in calendars:
                cal_id = calendar['id']
                cal_name = calendar.get('summary', 'Unnamed')
                primary = " (Primary)" if calendar.get('primary', False) else ""
                print(f"  • {cal_name}{primary}")
                print(f"    ID: {cal_id}")
            print("=" * 60)
            
            return calendars
            
        except Exception as e:
            self.logger.error(f"Failed to list calendars: {e}")
            return []


def test_google_calendar():
    """Test Google Calendar integration"""
    import sys
    
    print("=" * 60)
    print("Google Calendar Integration Test")
    print("=" * 60)
    
    if not GOOGLE_AVAILABLE:
        print("\n❌ Google Calendar libraries not installed!")
        print("\nInstall with:")
        print("  pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        sys.exit(1)
    
    print("\n📋 Initializing Google Calendar fetcher...")
    fetcher = GoogleCalendarFetcher()
    
    if not fetcher.service:
        print("\n❌ Failed to initialize Google Calendar service")
        print("\nMake sure you have:")
        print("  1. Created a project in Google Cloud Console")
        print("  2. Enabled Google Calendar API")
        print("  3. Downloaded credentials.json")
        print("  4. Placed credentials.json in the project root")
        sys.exit(1)
    
    print("✅ Connected to Google Calendar")
    
    # List calendars
    print("\n📅 Listing your calendars...")
    fetcher.list_calendars()
    
    # Fetch today's events
    print("\n📋 Fetching today's events...")
    events = fetcher.fetch_today_events()
    
    if events:
        print(f"\n✅ Found {len(events)} events:\n")
        for event in events:
            print(f"  🔔 {event.event_time.strftime('%H:%M')} - {event.title}")
            if event.description:
                print(f"     {event.description[:50]}...")
    else:
        print("\n📭 No events found for today")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_google_calendar()
