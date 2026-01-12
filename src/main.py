"""
Main Application Controller
Coordinates all components of the AI Reminder System
"""
import os
import sys
import yaml
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
from typing import List
import threading
import time

# Import modules
from event_fetcher import Event, EventFetcher
from display_manager import DisplayManager
from alarm_system import AlarmSystem
from voice_recognition import VoiceRecognition
from chatbot import Chatbot


class ReminderSystem:
    """Main application controller for the AI Reminder System"""
    
    def __init__(self, config_path: str = "config.yaml"):
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        self.logger.info("=" * 60)
        self.logger.info("AI Reminder System Starting")
        self.logger.info("=" * 60)
        
        # Initialize components
        self.event_fetcher = EventFetcher(self.config)
        self.display = DisplayManager(self.config)
        self.alarm_system = AlarmSystem(self.config)
        self.voice_recognition = VoiceRecognition(self.config)
        self.chatbot = Chatbot(self.config)
        
        # State
        self.events: List[Event] = []
        self.current_alarm_event = None
        self.running = False
        
        # Setup callbacks
        self.voice_recognition.on_command = self._handle_voice_command
        self.voice_recognition.on_text = self._handle_voice_text
        self.display.set_stop_alarm_callback(self._stop_alarm)
        
        # Background threads
        self.check_thread = None
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"Failed to load config: {e}")
            sys.exit(1)
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        log_file = log_config.get('file', 'logs/pibot.log')
        
        # Create logs directory if needed
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Configure root logger
        logger = logging.getLogger()
        logger.setLevel(log_level)
        
        # File handler with rotation
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=log_config.get('max_bytes', 10485760),
            backupCount=log_config.get('backup_count', 3)
        )
        file_handler.setLevel(log_level)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    def start(self):
        """Start the reminder system"""
        self.logger.info("Starting reminder system")
        self.running = True
        
        # Fetch initial events
        self._fetch_and_update_events()
        
        # Start voice recognition
        self.voice_recognition.start_listening()
        
        # Start background event checker
        self.check_thread = threading.Thread(
            target=self._event_check_loop,
            daemon=True
        )
        self.check_thread.start()
        
        # Update display status
        self.display.update_status("🟢 System Active - Listening", "#4ecca3")
        
        # Run GUI main loop
        self.logger.info("Starting GUI")
        try:
            self._run_gui_loop()
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
        finally:
            self.stop()
    
    def _run_gui_loop(self):
        """Run the GUI update loop"""
        refresh_interval = self.config['display'].get('refresh_interval', 60)
        last_refresh = time.time()
        
        while self.running:
            try:
                # Update GUI
                self.display.update()
                
                # Periodic refresh
                if time.time() - last_refresh >= refresh_interval:
                    self._fetch_and_update_events()
                    last_refresh = time.time()
                
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error in GUI loop: {e}")
                break
    
    def _fetch_and_update_events(self):
        """Fetch events from backend and update display"""
        self.logger.info("Fetching events")
        self.events = self.event_fetcher.fetch_today_events()
        self.display.update_events(self.events)
        self.logger.info(f"Loaded {len(self.events)} events")
    
    def _event_check_loop(self):
        """Background loop to check for events that need alarms"""
        while self.running:
            try:
                self._check_events()
                time.sleep(10)  # Check every 10 seconds
            except Exception as e:
                self.logger.error(f"Error in event check loop: {e}")
    
    def _check_events(self):
        """Check if any events need to trigger alarms"""
        now = datetime.now()
        
        for event in self.events:
            if event.triggered:
                continue
            
            # Check if event time has arrived (within 30 seconds)
            time_diff = (event.event_time - now).total_seconds()
            if -30 <= time_diff <= 0:
                self.logger.info(f"Triggering alarm for: {event.title}")
                self._trigger_event_alarm(event)
                event.triggered = True
                
                # Update backend
                self.event_fetcher.mark_event_triggered(event.id)
    
    def _trigger_event_alarm(self, event: Event):
        """Trigger an alarm for an event"""
        self.current_alarm_event = event
        self.display.show_alarm(event)
        self.alarm_system.trigger_alarm(event)
    
    def _handle_voice_command(self, command: str):
        """Handle voice commands"""
        self.logger.info(f"Voice command: {command}")
        
        if command == 'stop':
            self._stop_alarm()
    
    def _handle_voice_text(self, text: str):
        """Handle general voice text (for chatbot)"""
        self.logger.info(f"Voice text: {text}")
        
        # Check if alarm is active - prioritize stop command
        if self.alarm_system.is_playing:
            if 'stop' in text.lower():
                self._stop_alarm()
                return
        
        # Send to chatbot
        self.display.update_status("🤔 Processing...", "#f39c12")
        response = self.chatbot.chat(text)
        
        if response:
            self.logger.info(f"Chatbot response: {response}")
            self.alarm_system.speak_async(response)
            self.display.update_status(f"💬 {response[:50]}...", "#3498db")
        else:
            self.display.update_status("🟢 System Active - Listening", "#4ecca3")
    
    def _stop_alarm(self):
        """Stop the current alarm"""
        self.logger.info("Stopping alarm")
        self.alarm_system.stop_alarm()
        self.display.clear_alarm()
        self.current_alarm_event = None
        
        # Speak confirmation
        self.alarm_system.speak_async("Alarm stopped")
    
    def stop(self):
        """Stop the reminder system"""
        self.logger.info("Stopping reminder system")
        self.running = False
        
        # Stop components
        self.alarm_system.stop_alarm()
        self.voice_recognition.stop_listening()
        
        # Cleanup
        self.alarm_system.cleanup()
        self.voice_recognition.cleanup()
        
        self.logger.info("System stopped")


def main():
    """Main entry point"""
    # Check for config file
    config_file = "config.yaml"
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    
    if not os.path.exists(config_file):
        print(f"Error: Config file not found: {config_file}")
        sys.exit(1)
    
    # Create and start the system
    system = ReminderSystem(config_file)
    system.start()


if __name__ == "__main__":
    main()
