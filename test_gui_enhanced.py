"""
Enhanced GUI Test - Shows real-time status updates
This test demonstrates all event statuses:
- UPCOMING (blue) - More than 5 minutes away
- STARTING SOON (red) - Within 5 minutes
- IN PROGRESS (orange) - Currently happening (up to 60 min after start)
- COMPLETED (green) - Manually marked as done
- EXPIRED (gray) - More than 60 minutes past event time
"""
import sys
import yaml
from datetime import datetime, timedelta

sys.path.insert(0, 'src')

from event_fetcher import Event
from display_manager import DisplayManager

def main():
    print("=" * 60)
    print("AI Reminder System - Enhanced GUI Test")
    print("=" * 60)
    print("\nShowing events with different statuses:")
    print("  📅 UPCOMING - Future events (blue)")
    print("  🔔 STARTING SOON - Within 5 minutes (red highlight)")
    print("  ▶ IN PROGRESS - Currently happening (orange)")
    print("  ✓ COMPLETED - Marked as done (green)")
    print("  ✗ EXPIRED - Past events (gray)")
    print("\n✨ Statuses auto-update every 30 seconds")
    print("\nClose the window to exit...")
    print("=" * 60)
    
    # Load config
    config = yaml.safe_load(open('config.yaml'))
    
    # Create display
    display = DisplayManager(config)
    
    # Create sample events showing all statuses
    now = datetime.now()
    events = [
        # Starting soon (red highlight)
        Event('1', '🚨 Urgent Meeting', 'This is starting in 2 minutes!', now + timedelta(minutes=2)),
        
        # In progress (orange)
        Event('2', '💼 Current Meeting', 'Started 20 minutes ago, still ongoing', now - timedelta(minutes=20)),
        
        # Upcoming soon
        Event('3', '📞 Client Call', 'Scheduled in 10 minutes', now + timedelta(minutes=10)),
        
        # Future events (blue)
        Event('4', '🍽️ Lunch Meeting', 'Team lunch at the cafe', now + timedelta(hours=2)),
        Event('5', '📊 Project Review', 'Quarterly review meeting', now + timedelta(hours=4)),
        Event('6', '🎓 Training Session', 'New software training', now + timedelta(hours=6)),
        
        # Completed (green checkmark)
        Event('7', '✅ Daily Standup', 'Morning team sync - Done!', now - timedelta(minutes=30), triggered=True),
        
        # Expired (gray)
        Event('8', '📧 Email Review', 'This expired 2 hours ago', now - timedelta(hours=2)),
        Event('9', '☕ Coffee Break', 'Missed this one', now - timedelta(hours=5)),
    ]
    
    # Sort by time
    events.sort(key=lambda e: e.event_time)
    
    # Update display with events
    display.update_events(events)
    
    # Show status
    display.update_status(
        f"🟢 System Active - {len(events)} Events | Auto-refresh enabled", 
        "#4ecca3"
    )
    
    # Run GUI
    display.run()

if __name__ == "__main__":
    main()
