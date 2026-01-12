# Google Calendar Integration Setup Guide

## Prerequisites

### 1. Install Required Packages
```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### 2. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing one)
3. Enable **Google Calendar API**:
   - Click "Enable APIs and Services"
   - Search for "Google Calendar API"
   - Click "Enable"

### 3. Create OAuth 2.0 Credentials

1. In Google Cloud Console, go to **APIs & Services → Credentials**
2. Click **"+ CREATE CREDENTIALS"** → **OAuth client ID**
3. If prompted, configure the OAuth consent screen:
   - User Type: **External**
   - App name: "AI Reminder System"
   - User support email: Your email
   - Developer contact: Your email
   - Scopes: Add `https://www.googleapis.com/auth/calendar.readonly`
4. Create OAuth Client ID:
   - Application type: **Desktop app**
   - Name: "PiBot Reminder"
5. Click **"CREATE"**
6. Download the credentials JSON file
7. Rename it to **`credentials.json`**
8. Place it in your project root directory (`c:\Projects\AI\PiBot\credentials.json`)

## Usage

### Test Google Calendar Connection

```bash
python src/google_calendar_fetcher.py
```

This will:
1. Open your browser for Google authentication
2. Ask for permission to read your calendar
3. List your available calendars
4. Show today's events

### Run App with Google Calendar

Update `run_with_dummy_events.py`:

```python
"""
Run application with Google Calendar events
"""
import sys
sys.path.insert(0, 'src')

from google_calendar_fetcher import GoogleCalendarFetcher
from main import ReminderSystem
from event_fetcher import EventFetcher

# Override the fetch method to use Google Calendar
def patched_fetch_today_events(self):
    print("📅 Fetching events from Google Calendar...")
    fetcher = GoogleCalendarFetcher()
    return fetcher.fetch_today_events()

EventFetcher.fetch_today_events = patched_fetch_today_events

# Run the application
system = ReminderSystem('config.yaml')
system.start()
```

### Use Multiple Calendars

```python
from google_calendar_fetcher import GoogleCalendarFetcher

fetcher = GoogleCalendarFetcher()

# List all calendars
fetcher.list_calendars()

# Fetch from specific calendar
events = fetcher.fetch_today_events(calendar_id='your-calendar-id@gmail.com')
```

## Configuration

### Update config.yaml

```yaml
# Google Calendar Configuration (optional)
google_calendar:
  enabled: true
  credentials_file: "credentials.json"
  token_file: "token.json"
  calendar_id: "primary"  # or specific calendar ID
```

## Authentication Flow

### First Time Setup

1. Run the application
2. Browser will open automatically
3. Sign in to your Google account
4. Grant calendar read permission
5. Token is saved to `token.json`
6. Future runs use saved token (no browser popup)

### Token Refresh

- Token expires after some time
- Automatically refreshed when needed
- If refresh fails, re-authentication required
- Delete `token.json` to force re-authentication

## Troubleshooting

### Error: "credentials.json not found"
- Download credentials from Google Cloud Console
- Place in project root directory
- Ensure filename is exactly `credentials.json`

### Error: "Google Calendar API not enabled"
- Go to Google Cloud Console
- Navigate to APIs & Services
- Enable Google Calendar API

### Error: "Access denied"
- Check OAuth consent screen settings
- Add your email to test users (if app not published)
- Verify scopes include calendar.readonly

### Error: "Token expired"
- Delete `token.json`
- Run application again to re-authenticate

## Security Notes

### Protect Your Credentials

**⚠️ IMPORTANT:**
- **NEVER** commit `credentials.json` to version control
- **NEVER** commit `token.json` to version control
- Add to `.gitignore`:
  ```
  credentials.json
  token.json
  ```

### Scope Permissions

This integration uses **read-only** scope:
- `https://www.googleapis.com/auth/calendar.readonly`
- Cannot modify or delete events
- Safe for reminder system

## Features

### Supported Event Types

✅ **Regular events** - Time-based events
✅ **All-day events** - Converted to 9 AM reminders
✅ **Recurring events** - Fetches today's occurrence
✅ **Multi-calendar** - Fetch from any calendar
✅ **Event details** - Title, description, time

### Auto-Sync

Events are fetched:
- On application startup
- Every 60 seconds (configurable)
- Automatically detects new events
- Updates display in real-time

## Example Output

```
📅 Fetching events from Google Calendar...
✅ Connected to Google Calendar

📋 Available Calendars:
============================================================
  • Personal Calendar (Primary)
    ID: your-email@gmail.com
  • Work Calendar
    ID: work-calendar-id@group.calendar.google.com
  • Team Events
    ID: team-events@group.calendar.google.com
============================================================

📋 Fetching today's events...

✅ Found 4 events:

  🔔 09:00 - Morning Standup
     Daily team sync meeting
  🔔 12:00 - Lunch with Client
     Discuss project requirements
  🔔 14:00 - Code Review
     Review new feature implementation
  🔔 16:30 - Team Meeting
     Weekly retrospective
```

## Advanced Usage

### Filter Events by Keywords

```python
def fetch_filtered_events():
    fetcher = GoogleCalendarFetcher()
    all_events = fetcher.fetch_today_events()
    
    # Only get events with "meeting" in title
    meetings = [e for e in all_events if 'meeting' in e.title.lower()]
    return meetings
```

### Fetch from Multiple Calendars

```python
def fetch_all_calendars():
    fetcher = GoogleCalendarFetcher()
    all_events = []
    
    # Fetch from primary
    all_events.extend(fetcher.fetch_today_events('primary'))
    
    # Fetch from work calendar
    all_events.extend(fetcher.fetch_today_events('work@company.com'))
    
    # Sort by time
    all_events.sort(key=lambda e: e.event_time)
    return all_events
```

## Integration with Main App

### Option 1: Replace Backend Fetcher

Modify `src/main.py`:

```python
# Use Google Calendar instead of backend API
if config.get('google_calendar', {}).get('enabled', False):
    from google_calendar_fetcher import GoogleCalendarFetcher
    self.event_fetcher = GoogleCalendarFetcher()
```

### Option 2: Hybrid Approach

Use both Google Calendar and backend:

```python
def fetch_all_events():
    # Fetch from Google Calendar
    google_events = GoogleCalendarFetcher().fetch_today_events()
    
    # Fetch from backend
    backend_events = EventFetcher(config).fetch_today_events()
    
    # Combine and deduplicate
    all_events = google_events + backend_events
    return all_events
```

## Testing

### Test Script

```bash
# Install packages
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client

# Test connection
python src/google_calendar_fetcher.py
```

### Expected Output

1. Browser opens for authentication
2. Grant calendar access
3. See list of calendars
4. See today's events

## References

- [Google Calendar API Documentation](https://developers.google.com/calendar/api)
- [OAuth 2.0 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)
- [Python Quickstart](https://developers.google.com/calendar/api/quickstart/python)
