"""
Event Fetcher Module
Fetches events from the backend API
"""
import requests
import logging
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class Event:
    """Represents a reminder event"""
    id: str
    title: str
    description: str
    event_time: datetime
    triggered: bool = False
    
    def __str__(self):
        return f"{self.event_time.strftime('%H:%M')} - {self.title}"


class EventFetcher:
    """Fetches events from backend API"""
    
    def __init__(self, config: Dict):
        self.base_url = config['backend']['url']
        self.events_endpoint = config['backend']['events_endpoint']
        self.timeout = config['backend']['timeout']
        self.logger = logging.getLogger(__name__)
        
    def fetch_today_events(self) -> List[Event]:
        """Fetch today's events from backend"""
        try:
            url = f"{self.base_url}{self.events_endpoint}"
            self.logger.info(f"Fetching events from {url}")
            
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            events_data = response.json()
            events = []
            
            for event_dict in events_data.get('events', []):
                event = self._parse_event(event_dict)
                if event:
                    events.append(event)
            
            self.logger.info(f"Fetched {len(events)} events")
            return events
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch events: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error parsing events: {e}")
            return []
    
    def _parse_event(self, event_dict: Dict) -> Optional[Event]:
        """Parse event dictionary into Event object"""
        try:
            event_time_str = event_dict.get('event_time') or event_dict.get('time')
            
            # Parse ISO format or common formats
            if 'T' in event_time_str:
                event_time = datetime.fromisoformat(event_time_str.replace('Z', '+00:00'))
            else:
                event_time = datetime.strptime(event_time_str, '%Y-%m-%d %H:%M:%S')
            
            return Event(
                id=str(event_dict.get('id', '')),
                title=event_dict.get('title', 'Untitled Event'),
                description=event_dict.get('description', ''),
                event_time=event_time,
                triggered=event_dict.get('triggered', False)
            )
        except Exception as e:
            self.logger.error(f"Failed to parse event: {e}")
            return None
    
    def mark_event_triggered(self, event_id: str) -> bool:
        """Mark an event as triggered in the backend"""
        try:
            url = f"{self.base_url}/events/{event_id}/triggered"
            response = requests.post(url, timeout=self.timeout)
            response.raise_for_status()
            self.logger.info(f"Event {event_id} marked as triggered")
            return True
        except requests.RequestException as e:
            self.logger.error(f"Failed to mark event as triggered: {e}")
            return False
