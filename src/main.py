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
from news_fetcher import NewsFetcher

# Try importing Google Calendar fetcher
try:
    from google_calendar_fetcher import GoogleCalendarFetcher
    GOOGLE_CALENDAR_AVAILABLE = True
except ImportError:
    GOOGLE_CALENDAR_AVAILABLE = False
    logging.warning("Google Calendar not available - install packages: pip install google-auth-oauthlib google-api-python-client")


class ReminderSystem:
    """Main application controller for the AI Reminder System"""
    
    def __init__(self, config_path: str = "config.yaml", secrets_path: str = "secrets.yaml"):
        # Load configuration
        self.config = self._load_config(config_path)
        self.secrets = self._load_secrets(secrets_path)

        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        self.logger.info("=" * 60)
        self.logger.info("AI Reminder System Starting")
        self.logger.info("=" * 60)

        # Set system volume from config if available
        system_cfg = self.config.get('system', {})
        default_volume = system_cfg.get('default_volume')
        if default_volume is not None:
            try:
                # Clamp value between 0 and 100
                vol = max(0, min(100, int(default_volume)))
                os.system(f"amixer set Master {vol}%")
                self.logger.info(f"System volume set to {vol}% from config.yaml")
            except Exception as e:
                self.logger.warning(f"Failed to set system volume: {e}")

        # Initialize components
        # Choose event source based on config
        event_source = self.config.get('event_source', 'backend')
        if event_source == 'google_calendar' and GOOGLE_CALENDAR_AVAILABLE:
            self.logger.info("Using Google Calendar as event source")
            self.event_fetcher = GoogleCalendarFetcher()
        else:
            if event_source == 'google_calendar':
                self.logger.warning("Google Calendar requested but not available, falling back to backend API")
            self.logger.info("Using Backend API as event source")
            self.event_fetcher = EventFetcher(self.config)

        self.display = DisplayManager(self.config)
        self.alarm_system = AlarmSystem(self.config, self.display)
        self.voice_recognition = VoiceRecognition(self.config)
        self.display.voice_recognition = self.voice_recognition  # Ensure display can process audio queue
        self.chatbot = Chatbot(self.config, self.secrets)
        self.news_fetcher = NewsFetcher(self.config)

        # State
        self.events: List[Event] = []
        self.current_alarm_event = None
        self.running = False

        # Setup callbacks
        self.voice_recognition.on_command = self._handle_voice_command
        self.voice_recognition.on_text = self._handle_voice_text
        self.display.set_stop_alarm_callback(self._stop_alarm)
        self.display.set_news_callbacks(self._fetch_news, self._read_news)
        self.display.set_config_callback(self._save_configuration)

        # Background threads
        self.check_thread = None

        # News TTS queue and worker
        self.news_tts_queue = []
        self.news_tts_thread = None
        self.news_tts_stop_event = threading.Event()
        self.news_cancel_token = 0  # Sync with display_manager
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"Failed to load config: {e}")
            sys.exit(1)
    
    def _load_secrets(self, secrets_path: str) -> dict:
        """Load secrets from YAML file"""
        try:
            if os.path.exists(secrets_path):
                with open(secrets_path, 'r', encoding='utf-8') as f:
                    secrets = yaml.safe_load(f)
                return secrets or {}
            else:
                print(f"Warning: Secrets file not found at {secrets_path}")
                return {}
        except Exception as e:
            print(f"Warning: Failed to load secrets: {e}")
            return {}
    
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
        
        # File handler with rotation and UTF-8 encoding
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=log_config.get('max_bytes', 10485760),
            backupCount=log_config.get('backup_count', 3),
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        
        # Console handler with error handling for non-UTF8 terminals
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        # Try to reconfigure stdout for UTF-8
        if hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            except:
                pass
        
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
        
        # Auto-fetch news on startup
        self.logger.info("Fetching initial news on startup")
        self._fetch_news()
        
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

                # Check for session timeout (silence)
                if self.voice_recognition.session_active:
                    if not self.voice_recognition.is_session_active():
                        self.logger.info("Session timed out due to silence. Disabling session.")
                        self.voice_recognition.disable_session()
                        self.chatbot.clear_history()
                        self.display.update_status("🟢 Session ended due to silence", "#4ecca3")

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
            # Check if event time has arrived (within 30 seconds)
            time_diff = (event.event_time - now).total_seconds()
            
            # Trigger alarm if:
            # 1. Event time has arrived (within 30 seconds of start time)
            # 2. Event hasn't been triggered yet
            if -30 <= time_diff <= 0 and not event.triggered:
                self.logger.info(f"Triggering alarm for: {event.title}")
                self._trigger_event_alarm(event)
                event.triggered = True
                
                # Update backend
                self.event_fetcher.mark_event_triggered(event.id)
            
            # Re-trigger for in-progress events if alarm was stopped
            # Events are considered "in progress" if they started but haven't passed yet
            # and no alarm is currently playing
            elif event.triggered and not self.alarm_system.is_playing:
                # Check if event is still within a reasonable time window
                # Re-trigger if event started less than auto_stop_after seconds ago
                auto_stop_after = self.config['alarm'].get('auto_stop_after', 1800)
                time_since_event = (now - event.event_time).total_seconds()
                
                if 0 <= time_since_event < auto_stop_after:
                    self.logger.info(f"Re-triggering alarm for in-progress event: {event.title}")
                    self._trigger_event_alarm(event)
    
    def _trigger_event_alarm(self, event: Event):
        """Trigger an alarm for an event"""
        self.current_alarm_event = event
        # Use after() to schedule GUI update on main thread
        try:
            self.display.root.after(0, lambda: self.display.show_alarm(event))
        except Exception as e:
            self.logger.error(f"Error showing alarm in GUI: {e}")
        self.alarm_system.trigger_alarm(event)
    
    def _handle_voice_command(self, command: str):
        """Handle voice commands"""
        self.logger.info(f"Voice command: {command}")
        
        if command == 'stop':
            self._stop_alarm()
    
    def _handle_voice_text(self, text: str):
        """Handle general voice text (for chatbot, session-aware)"""
        # Remove verbose debug/info logs for production
        # self.logger.info(f"[DEBUG] Voice text received for chatbot: {text}")

        # Check if alarm is active - prioritize stop command
        if self.alarm_system.is_playing:
            if 'stop' in text.lower():
                self.logger.info("[DEBUG] Stop command detected during alarm.")
                self._stop_alarm()
                return
        # Stop auto-reading news if 'stop' is said
        if 'stop' in text.lower() and hasattr(self.display, 'stop_auto_read'):
            # Set auto_read_active to False immediately for atomic interruption
            if hasattr(self.display, 'auto_read_active'):
                self.display.auto_read_active = False
            self.display.stop_auto_read()
            self.stop_news_tts()
            self.logger.info("[DEBUG] Stop command detected: Stopping auto-read news and TTS queue.")
            self.alarm_system.stop_speaking()
            return

        # Only stop speaking if:
        # 1. Chat session is enabled and user is chatting with LLM
        # 2. User is using stop command
        # 3. User is using wakeup words
        should_stop = False
        if self.voice_recognition.is_session_active():
            should_stop = True
        elif any(text.lower().startswith(w) for w in self.voice_recognition.wake_words):
            should_stop = True
        elif self.voice_recognition.stop_command in text.lower():
            should_stop = True
        if should_stop:
            self.alarm_system.stop_speaking()

        # Only process chatbot if session is active
        if self.voice_recognition.is_session_active():
            self.display.update_status("🤔 Processing...", "#f39c12")
            self.logger.info(f"[DEBUG] Sending to chatbot (provider: {self.chatbot.provider}): {text}")
            response = self.chatbot.chat(text)
            self.logger.info(f"[DEBUG] Chatbot raw response: {response}")

            if response:
                self.alarm_system.speak_async(response)
                self.display.update_status(f"💬 {response[:50]}...", "#3498db")
            else:
                self.logger.info("[DEBUG] No chatbot response, returning to listening state.")
                self.display.update_status("🟢 System Active - Listening", "#4ecca3")
        else:
            self.display.update_status("🟢 System Active - Listening", "#4ecca3")

        # Only clear chatbot history when session is explicitly disabled
        if self.voice_recognition.session_active:
            self.last_session_state = True
        else:
            if hasattr(self, 'last_session_state') and self.last_session_state:
                self.chatbot.clear_history()
                self.last_session_state = False

        # Add voice command to enable RSS news reading
        for wake_word in self.voice_recognition.wake_words:
            if text.lower().startswith(wake_word + " news") or text.lower().startswith(wake_word + " read news"):
                self.logger.info("Voice command detected: Enable RSS news reading")
                self._fetch_news()
                return
    
    def _stop_alarm(self):
        """Stop the current alarm"""
        self.logger.info("Stopping alarm")
        self.alarm_system.stop_alarm()
        self.display.clear_alarm()
        self.current_alarm_event = None
        
        # Speak confirmation
        self.alarm_system.speak_async("Alarm stopped")
    
    def _fetch_news(self):
        """Fetch news from RSS feeds"""
        self.logger.info("Fetching news from RSS feeds")
        self.display.update_status("📰 Fetching news...", "#3498db")
        
        try:
            # Fetch news directly (it's fast enough)
            news_items = self.news_fetcher.fetch_news(max_items_per_feed=5)
            self._on_news_fetched(news_items)
            
        except Exception as e:
            self.logger.error(f"Error fetching news: {e}")
            self.display.update_status(f"❌ Error fetching news", "#e94560")
    
    def _on_news_fetched(self, news_items):
        """Handle news fetch completion"""
        self.display.update_news(news_items)
        self.display.update_status(f"✅ Fetched {len(news_items)} news items", "#4ecca3")
        self.logger.info(f"News fetched: {len(news_items)} items")
        
        # Auto-start reading news
        if news_items:
            self.display.start_auto_read()
    
    def _read_news(self, news_item, auto_advance=False):
        """Read a news item using TTS via a single-threaded, interruptible queue."""
        # Capture cancel token at scheduling time
        cancel_token = getattr(self.display, '_news_cancel_token', 0)
        self.news_tts_queue.append((news_item, auto_advance, cancel_token))
        if not self.news_tts_thread or not self.news_tts_thread.is_alive():
            self.news_tts_stop_event.clear()
            self.news_tts_thread = threading.Thread(target=self._news_tts_worker, daemon=True)
            self.news_tts_thread.start()

    def _news_tts_worker(self):
        while self.news_tts_queue and not self.news_tts_stop_event.is_set():
            news_item, auto_advance, scheduled_token = self.news_tts_queue.pop(0)
            # Check cancellation token before TTS
            current_token = getattr(self.display, '_news_cancel_token', 0)
            if scheduled_token != current_token:
                self.logger.info("[QUEUE] News TTS cancelled by token (before TTS)")
                break
            if hasattr(self.display, 'auto_read_active') and not self.display.auto_read_active:
                self.logger.info("_news_tts_worker: Auto-read not active, aborting news read.")
                break
            text_to_read = f"News from {news_item.source}. {news_item.title}. {news_item.description}."
            try:
                self.logger.info(f"[QUEUE] Starting TTS (auto_advance={auto_advance})")
                self.alarm_system._speak(text_to_read)
                # Check cancellation token after TTS
                current_token = getattr(self.display, '_news_cancel_token', 0)
                if scheduled_token != current_token:
                    self.logger.info("[QUEUE] News TTS cancelled by token (after TTS)")
                    break
                auto_advance_now = auto_advance and getattr(self.display, 'auto_read_active', False)
                self.logger.info(f"[QUEUE] TTS completed, checking auto_advance: {auto_advance_now}")
                if self.news_tts_stop_event.is_set() or not getattr(self.display, 'auto_read_active', False):
                    self.logger.info("[QUEUE] Stop event set or auto_read_active is False after TTS; not advancing.")
                    break
                if auto_advance_now:
                    self.logger.info("[QUEUE] Waiting 2 seconds before advancing...")
                    import time
                    time.sleep(2)
                    # Check cancellation token before scheduling auto-advance
                    current_token = getattr(self.display, '_news_cancel_token', 0)
                    if scheduled_token != current_token:
                        self.logger.info("[QUEUE] News TTS cancelled by token (before auto-advance)")
                        break
                    if self.news_tts_stop_event.is_set() or not getattr(self.display, 'auto_read_active', False):
                        self.logger.info("[QUEUE] Stop event set or auto_read_active is False after wait; not scheduling auto-advance.")
                        break
                    self.logger.info("[QUEUE] Scheduling auto-advance to next news")
                    self.display.schedule_auto_advance()
                else:
                    self.logger.info("[QUEUE] Auto-advance is False, not advancing")
            except Exception as e:
                self.logger.error(f"[QUEUE] Error in TTS: {e}")

    def stop_news_tts(self):
        """Immediately stop all queued and running news TTS, and clear any pending auto-advance."""
        self.news_tts_stop_event.set()
        self.news_tts_queue.clear()
        # Sync cancellation token with display_manager
        if hasattr(self.display, '_news_cancel_token'):
            self.display._news_cancel_token += 1
        self.logger.info("stop_news_tts: Cleared news TTS queue, set stop event, incremented cancel token.")
        # Attempt to clear any pending auto-advance in display_manager
        if hasattr(self.display, 'clear_pending_auto_advance'):
            self.display.clear_pending_auto_advance()
    
    def _save_configuration(self, config_values: dict):
        """Save configuration changes to files"""
        import yaml
        
        try:
            # Separate secrets from config
            secrets_to_save = {}
            config_to_save = dict(self.config)  # Make a copy
            
            for key, value in config_values.items():
                if key in ['openai_api_key', 'gemini_api_key']:
                    # Save to secrets
                    secrets_to_save[key] = value
                elif key == 'news.feeds':
                    # Handle news feeds dictionary specially
                    if 'news' not in config_to_save:
                        config_to_save['news'] = {}
                    config_to_save['news']['feeds'] = value
                else:
                    # Save to config
                    keys = key.split('.')
                    current = config_to_save
                    
                    # Navigate to the nested dict
                    for k in keys[:-1]:
                        if k not in current:
                            current[k] = {}
                        current = current[k]
                    
                    # Convert numeric values
                    final_key = keys[-1]
                    if key in ['tts.rate', 'alarm.voice_reminder_interval', 'alarm.auto_stop_after', 'news.max_items_per_feed']:
                        try:
                            current[final_key] = int(value)
                        except ValueError:
                            current[final_key] = value
                    elif key in ['tts.volume']:
                        try:
                            current[final_key] = float(value)
                        except ValueError:
                            current[final_key] = value
                    else:
                        current[final_key] = value
            
            # Write config.yaml
            with open('config.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(config_to_save, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            # Write secrets.yaml
            if secrets_to_save:
                with open('secrets.yaml', 'w', encoding='utf-8') as f:
                    f.write("# API Keys and Secrets Configuration\n")
                    f.write("# DO NOT COMMIT THIS FILE TO VERSION CONTROL\n\n")
                    for key, value in secrets_to_save.items():
                        f.write(f"# {key.replace('_', ' ').title()}\n")
                        f.write(f'{key}: "{value}"\n\n')
            
            self.logger.info("Configuration saved successfully")
            
            # Update internal config
            self.config = config_to_save
            self.secrets.update(secrets_to_save)
            
            # Apply configuration changes immediately
            self._apply_config_changes(config_values, secrets_to_save)
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
    
    def _apply_config_changes(self, config_values: dict, secrets_changes: dict):
        """Apply configuration changes to running components"""
        try:
            # Update TTS settings in alarm system
            if any(key.startswith('tts.') for key in config_values.keys()):
                self.logger.info("Updating TTS settings...")
                self.alarm_system.tts_config = self.config['tts']
                self.alarm_system.update_tts_settings()
            
            # Update alarm settings
            if any(key.startswith('alarm.') for key in config_values.keys()):
                self.logger.info("Updating alarm settings...")
                self.alarm_system.alarm_config = self.config['alarm']
            
            # Update chatbot if API keys changed
            if secrets_changes:
                self.logger.info("Updating chatbot with new API keys...")
                self.chatbot.secrets = self.secrets
                # Reinitialize chatbot client
                provider_name = self.config['chatbot'].get('provider', 'openai').lower()
                if provider_name == 'openai':
                    self.chatbot._init_openai()
                else:
                    self.chatbot._init_gemini()
            
            # Update chatbot provider/model if changed
            if any(key.startswith('chatbot.') for key in config_values.keys()):
                self.logger.info("Updating chatbot settings...")
                self.chatbot.config = self.config['chatbot']
                # Reinitialize if provider changed
                if 'chatbot.provider' in config_values:
                    provider_name = config_values['chatbot.provider'].lower()
                    from chatbot import ChatProvider
                    self.chatbot.provider = ChatProvider.OPENAI if provider_name == 'openai' else ChatProvider.GEMINI
                    if self.chatbot.provider == ChatProvider.OPENAI:
                        self.chatbot._init_openai()
                    else:
                        self.chatbot._init_gemini()
            
            # Update news fetcher if feeds changed
            if 'news.feeds' in config_values or 'news.max_items_per_feed' in config_values:
                self.logger.info("Updating news fetcher settings...")
                self.news_fetcher.config = self.config
                self.news_fetcher.feeds = self.config['news']['feeds']
                self.logger.info(f"News feeds updated: {len(self.news_fetcher.feeds)} feeds active")
            
            self.logger.info("Configuration changes applied successfully")
            
        except Exception as e:
            self.logger.error(f"Error applying configuration changes: {e}")
    
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
