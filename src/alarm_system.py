"""
Alarm System Module
Handles alarm sounds and Text-to-Speech
"""
import os
import sys
import platform
import logging
import threading
from typing import Optional
from datetime import datetime
import tempfile
import pygame
import pyttsx3
from gtts import gTTS
from event_fetcher import Event


class AlarmSystem:
    def stop_speaking(self):
        """Interrupt any ongoing TTS playback (gTTS/pygame or pyttsx3)"""
        # Interrupt gTTS/pygame playback
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        # Interrupt pyttsx3 playback
        if self.tts_engine:
            try:
                self.tts_engine.stop()
            except Exception:
                pass

    """Manages alarm sounds and text-to-speech notifications"""
    
    def __init__(self, config: dict, display_manager=None):
        self.config = config
        self.alarm_config = config['alarm']
        self.tts_config = config['tts']
        self.logger = logging.getLogger(__name__)
        
        # Reference to display manager for showing speech text
        self.display_manager = display_manager
        
        # Detect OS for TTS method selection
        self.is_windows = platform.system() == 'Windows'
        self.logger.info(f"Running on {platform.system()}, using {'Windows SAPI' if self.is_windows else 'Linux TTS'}")
        
        # Initialize pygame for sound
        pygame.mixer.init()
        self.alarm_sound = None
        self._load_alarm_sound()
        
        # Initialize TTS engine
        self.tts_engine = self._init_tts()
        
        # TTS lock to prevent concurrent access
        self.tts_lock = threading.Lock()
        
        # State
        self.is_playing = False
        self.alarm_thread: Optional[threading.Thread] = None
        self.stop_flag = threading.Event()
        self.current_event: Optional[Event] = None
        self.last_voice_reminder = None
        
    def _load_alarm_sound(self):
        """Load the alarm sound file"""
        sound_file = self.alarm_config.get('sound_file')
        if sound_file and os.path.exists(sound_file):
            try:
                self.alarm_sound = pygame.mixer.Sound(sound_file)
                volume = self.alarm_config.get('volume', 0.8)
                self.alarm_sound.set_volume(volume)
                self.logger.info(f"Loaded alarm sound: {sound_file}")
            except Exception as e:
                self.logger.error(f"Failed to load alarm sound: {e}")
        else:
            self.logger.warning("No alarm sound file configured or file not found")
    
    def _init_tts(self) -> pyttsx3.Engine:
        """Initialize text-to-speech engine"""
        try:
            engine = pyttsx3.init(debug=False)
            
            # Configure voice
            rate = self.tts_config.get('rate', 150)
            volume = self.tts_config.get('volume', 0.9)
            voice_id = self.tts_config.get('voice')
            
            engine.setProperty('rate', rate)
            engine.setProperty('volume', volume)
            
            if voice_id:
                engine.setProperty('voice', voice_id)
            
            # Don't start the loop - we'll use runAndWait() instead
            # engine.startLoop(False)  # Removed to avoid "run loop already started" error
            
            self.logger.info("TTS engine initialized")
            return engine
            
        except Exception as e:
            self.logger.error(f"Failed to initialize TTS: {e}")
            return None
    
    def update_tts_settings(self):
        """Update TTS settings without reinitializing the engine"""
        try:
            if self.tts_engine:
                rate = self.tts_config.get('rate', 150)
                volume = self.tts_config.get('volume', 0.9)
                
                self.tts_engine.setProperty('rate', rate)
                self.tts_engine.setProperty('volume', volume)
                
                self.logger.info(f"TTS settings updated: rate={rate}, volume={volume}")
        except Exception as e:
            self.logger.error(f"Failed to update TTS settings: {e}")
    
    def trigger_alarm(self, event: Event):
        """Trigger an alarm for an event"""
        if self.is_playing:
            self.logger.warning("Alarm already playing")
            return
        
        self.logger.info(f"Triggering alarm for event: {event.title}")
        self.is_playing = True
        self.stop_flag.clear()
        
        # Start alarm in separate thread
        self.alarm_thread = threading.Thread(
            target=self._alarm_loop,
            args=(event,),
            daemon=True
        )
        self.alarm_thread.start()
    
    def _alarm_loop(self, event: Event):
        """Main alarm loop (runs in separate thread)"""
        try:
            self.current_event = event
            start_time = datetime.now()
            self.last_voice_reminder = start_time
            
            # Initial announcement
            print(f"\n{'='*60}")
            print(f"🔔 VOICE REMINDER TRIGGERED")
            print(f"{'='*60}")
            print(f"Event: {event.title}")
            print(f"Description: {event.description or 'None'}")
            print(f"Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}\n")
            
            print(f"🗣️  About to speak title...")
            self._speak(f"Reminder: {event.title}")
            print(f"✅ Title spoken")
            
            if event.description:
                print(f"🗣️  About to speak description...")
                self._speak(event.description)
                print(f"✅ Description spoken")
            
            print(f"✅ Initial announcement complete\n")
            
            # Get intervals
            sound_repeat_interval = self.alarm_config.get('repeat_interval', 30)
            voice_reminder_interval = self.alarm_config.get('voice_reminder_interval', 300)
            auto_stop_after = self.alarm_config.get('auto_stop_after', 1800)
            
            print(f"📋 Loop settings: voice_interval={voice_reminder_interval}s, auto_stop={auto_stop_after}s\n")
            
            while not self.stop_flag.is_set():
                print(f"🔄 Loop iteration started...")
                now = datetime.now()
                elapsed = (now - start_time).total_seconds()
                
                # Check auto-stop timeout
                if elapsed >= auto_stop_after:
                    self.logger.info("Alarm auto-stopped after timeout")
                    print(f"\n⏰ Auto-stopped after {auto_stop_after}s\n")
                    break
                
                # Check if voice reminder is due
                time_since_last_voice = (now - self.last_voice_reminder).total_seconds()
                
                # Debug: Always show status
                print(f"\r⏲️  Checking... Time since last voice: {int(time_since_last_voice)}s / {voice_reminder_interval}s needed", end='', flush=True)
                
                if time_since_last_voice >= voice_reminder_interval:
                    self.logger.info(f"Voice reminder due (every {voice_reminder_interval}s)")
                    
                    # Debug output
                    print(f"\n{'='*60}")
                    print(f"🔁 REPEATING VOICE REMINDER")
                    print(f"{'='*60}")
                    print(f"Event: {event.title}")
                    print(f"Description: {event.description or 'None'}")
                    print(f"Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"Elapsed: {int((now - start_time).total_seconds())}s")
                    print(f"Next reminder in: {voice_reminder_interval}s")
                    print(f"{'='*60}\n")
                    
                    self._speak(f"Reminder: {event.title}")
                    if event.description:
                        self._speak(event.description)
                    self.last_voice_reminder = now
                
                # No beep sound - only voice reminders
                if self.stop_flag.is_set():
                    break
                
                # Wait and check voice reminder timing every 10 seconds
                self.stop_flag.wait(10)
            
        except Exception as e:
            self.logger.error(f"Error in alarm loop: {e}")
            print(f"\n❌ ERROR in alarm loop: {e}\n")
        finally:
            self.is_playing = False
            self.current_event = None
            self.last_voice_reminder = None
            self.logger.info("Alarm stopped")
            print(f"✅ Alarm loop finished\n")
    
    def stop_alarm(self):
        """Stop the currently playing alarm"""
        if not self.is_playing:
            return
        
        self.logger.info("Stopping alarm")
        self.stop_flag.set()
        
        # Stop any playing sounds
        pygame.mixer.stop()
        
        # Wait for thread to finish
        if self.alarm_thread and self.alarm_thread.is_alive():
            self.alarm_thread.join(timeout=2)
        
        self.is_playing = False
    
    def _contains_chinese(self, text: str) -> bool:
        """Check if text contains Chinese characters"""
        return any('\u4e00' <= char <= '\u9fff' for char in text)
    
    def _speak(self, text: str):
        """Speak text using TTS"""
        if not self.tts_engine:
            self.logger.warning("TTS engine not available")
            print("⚠️  TTS engine not available")
            return
        
        # Use lock to ensure only one TTS operation at a time
        with self.tts_lock:
            try:
                print(f"🔊 Speaking: {text}")
                self.logger.info(f"Speaking: {text}")
                
                # Show text on GUI if display manager is available
                if self.display_manager:
                    self.display_manager.show_speaking_text(text)
                
                # Use Windows-specific TTS on Windows
                if self.is_windows:
                    self._speak_windows(text)
                else:
                    self._speak_linux(text)
                
                # Hide speaking text after speech completes
                if self.display_manager:
                    self.display_manager.hide_speaking_text()
                
                print(f"✅ Finished speaking")
                    
            except Exception as e:
                self.logger.error(f"TTS error: {e}")
                print(f"❌ TTS error: {e}")
    
    def _speak_windows(self, text: str):
        """Speak text using Windows SAPI"""
        import win32com.client
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        
        # Detect if text contains Chinese characters
        is_chinese = self._contains_chinese(text)
        if is_chinese:
            voice_name = self.tts_config.get('chinese_voice_name', 'Microsoft Huihui Desktop')
        else:
            voice_name = self.tts_config.get('voice_name')
        
        # Try to find and set the voice by name
        if voice_name:
            voices = speaker.GetVoices()
            for i in range(voices.Count):
                voice = voices.Item(i)
                if voice_name in voice.GetDescription():
                    speaker.Voice = voice
                    self.logger.info(f"Using voice: {voice.GetDescription()}")
                    break
        
        # Configure voice settings
        rate = self.tts_config.get('rate', 150)
        volume = self.tts_config.get('volume', 0.9)
        
        # SAPI rate is -10 to 10, pyttsx3 is ~100-200
        # Convert: pyttsx3 150 = SAPI 0
        sapi_rate = int((rate - 150) / 15)  # -10 to 10 range
        sapi_rate = max(-10, min(10, sapi_rate))
        
        speaker.Rate = sapi_rate
        speaker.Volume = int(volume * 100)  # 0-100
        
        # Speak (this is synchronous)
        self.logger.info(f"Using Windows SAPI for {'Chinese' if is_chinese else 'English'} text")
        speaker.Speak(text)
    
    def _speak_linux(self, text: str):
        """Speak text using Linux TTS (gTTS for better quality voices)"""
        # Use gTTS for both Chinese and English for better quality
        if self._contains_chinese(text):
            # Use gTTS for Chinese text
            self.logger.info("Using gTTS for Chinese text")
            lang = 'zh-CN'
        else:
            # Use gTTS for English text with better female voice
            self.logger.info("Using gTTS for English text")
            lang = 'en'
        
        try:
            tts = gTTS(text=text, lang=lang, slow=False)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                temp_file = fp.name
                tts.save(temp_file)
            
            # Play the audio file using pygame
            try:
                pygame.mixer.music.load(temp_file)
                volume = self.tts_config.get('volume', 0.9)
                pygame.mixer.music.set_volume(volume)
                pygame.mixer.music.play()
                
                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_file)
                except:
                    pass
        except Exception as e:
            self.logger.error(f"gTTS error: {e}, falling back to pyttsx3")
            # Fallback to pyttsx3 if gTTS fails
            rate = self.tts_config.get('rate', 150)
            volume = self.tts_config.get('volume', 0.9)
            
            self.tts_engine.setProperty('rate', rate)
            self.tts_engine.setProperty('volume', volume)
            
            # Speak (synchronous)
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
    
    def speak_async(self, text: str):
        """Speak text asynchronously, interrupting any current speech"""
        self.stop_speaking()  # Interrupt any ongoing TTS
        thread = threading.Thread(
            target=self._speak,
            args=(text,),
            daemon=True
        )
        thread.start()
    
    def test_alarm(self):
        """Test the alarm system"""
        self.logger.info("Testing alarm system")
        self._speak("Alarm system test")
        if self.alarm_sound:
            self.alarm_sound.play()
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_alarm()
        pygame.mixer.quit()
        if self.tts_engine:
            try:
                self.tts_engine.endLoop()
                self.tts_engine.stop()
            except:
                pass
