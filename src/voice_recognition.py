"""
Voice Recognition Module
Handles speech recognition using Vosk or Whisper
"""
import os
import logging
import threading
import queue
from typing import Optional, Callable
import pyaudio
import json

# Try importing Vosk
try:
    from vosk import Model, KaldiRecognizer
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    logging.warning("Vosk not available")

# Try importing SpeechRecognition (for Whisper)
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False
    logging.warning("SpeechRecognition not available")


class VoiceRecognition:
    """Manages voice recognition for commands and chatbot"""
    
    def __init__(self, config: dict):
        self.config = config['speech']
        self.logger = logging.getLogger(__name__)

        # Audio configuration (must be set before recognizer init)
        self.sample_rate = self.config.get('sample_rate', 16000)
        self.device_index = self.config.get('device_index')

        # Initialize recognizer
        self.engine = self.config.get('engine', 'vosk').lower()
        self.recognizer = None
        self.model = None

        if self.engine == 'vosk':
            self._init_vosk()
        elif self.engine == 'whisper':
            self._init_whisper()

        # PyAudio
        self.audio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None

        # Recognition state
        self.is_listening = False
        self.listen_thread: Optional[threading.Thread] = None
        self.audio_queue = queue.Queue()

        # Callbacks
        self.on_command: Optional[Callable[[str], None]] = None
        self.on_text: Optional[Callable[[str], None]] = None

        # Wake words and commands
        # Support multiple wake words: 'assistant', 'hellen', 'pi', 'hello'
        wake_words = self.config.get('wake_word', ['assistant', 'hellen', 'pi', 'hello'])
        if isinstance(wake_words, str):
            self.wake_words = [wake_words.lower()]
        else:
            self.wake_words = [w.lower() for w in wake_words]
        self.stop_command = self.config.get('stop_command', 'stop').lower()

        # Session state for LLM chat
        self.session_active = False
        self.last_session_time = None
        self.session_timeout = 60  # seconds

    def is_session_active(self):
        """Check if session is active and not timed out"""
        if not self.session_active:
            return False
        if self.last_session_time is None:
            return False
        import time
        if time.time() - self.last_session_time > self.session_timeout:
            self.session_active = False
            return False
        return True

    def enable_session(self):
        """Enable LLM chat session"""
        import time
        self.session_active = True
        self.last_session_time = time.time()
        self.logger.info("LLM chat session ENABLED")

    def disable_session(self):
        """Disable LLM chat session"""
        self.session_active = False
        self.last_session_time = None
        self.logger.info("LLM chat session DISABLED")
        
    def _init_vosk(self):
        """Initialize Vosk speech recognition with debug info"""
        self.logger.debug(f"VOSK_AVAILABLE: {VOSK_AVAILABLE}")
        if not VOSK_AVAILABLE:
            self.logger.error("Vosk is not installed")
            return

        model_path = self.config.get('model_path')
        self.logger.debug(f"Configured model_path: {model_path}")
        if not model_path or not os.path.exists(model_path):
            self.logger.error(f"Vosk model not found: {model_path}")
            return

        self.logger.debug(f"Sample rate: {self.sample_rate}")
        self.logger.debug(f"Device index: {self.device_index}")
        try:
            self.model = Model(model_path)
            self.logger.debug("Vosk Model loaded successfully")
            self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
            self.logger.debug("KaldiRecognizer created successfully")
            self.recognizer.SetWords(True)
            self.logger.info("Vosk initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Vosk: {e}")
    
    def _init_whisper(self):
        """Initialize Whisper speech recognition"""
        if not SR_AVAILABLE:
            self.logger.error("SpeechRecognition is not installed")
            return
        
        try:
            self.recognizer = sr.Recognizer()
            self.logger.info("Whisper initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Whisper: {e}")
    
    def start_listening(self):
        """Start listening for voice commands"""
        if self.is_listening:
            self.logger.warning("Already listening")
            return
        
        if not self.recognizer:
            self.logger.error("Recognizer not initialized")
            return
        
        self.logger.info("Starting voice recognition")
        self.is_listening = True
        
        # Start audio stream
        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=4000
            )
            
            # Start listening thread
            self.listen_thread = threading.Thread(
                target=self._listen_loop,
                daemon=True
            )
            self.listen_thread.start()
            
        except Exception as e:
            self.logger.error(f"Failed to start audio stream: {e}")
            self.is_listening = False
    
    def stop_listening(self):
        """Stop listening for voice commands"""
        if not self.is_listening:
            return
        
        self.logger.info("Stopping voice recognition")
        self.is_listening = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        if self.listen_thread:
            self.listen_thread.join(timeout=2)
    
    def _listen_loop(self):
        """Main listening loop (runs in separate thread)"""
        if self.engine == 'vosk':
            self._vosk_listen_loop()
        elif self.engine == 'whisper':
            self._whisper_listen_loop()
    
    def _vosk_listen_loop(self):
        """Vosk listening loop (thread-safe, uses queue)"""
        try:
            while self.is_listening and self.stream:
                data = self.stream.read(4000, exception_on_overflow=False)

                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get('text', '').lower().strip()

                    if text:
                        print(f"[VOSK] Recognized: {text}")
                        self.logger.debug(f"Recognized: {text}")
                        # Instead of calling _process_text directly, put in queue
                        self.audio_queue.put(text)

        except Exception as e:
            self.logger.error(f"Error in Vosk listen loop: {e}")
        finally:
            self.is_listening = False

    def process_pending_audio(self):
        """Process any recognized text from the audio queue (to be called from main thread)"""
        # self.logger.info("[INFO] process_pending_audio called")
        while not self.audio_queue.empty():
            text = self.audio_queue.get()
            self.logger.info(f"[INFO] process_pending_audio got text: {text}")
            self._process_text(text)
    
    def _whisper_listen_loop(self):
        """Whisper listening loop"""
        try:
            with sr.Microphone(sample_rate=self.sample_rate, device_index=self.device_index) as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                while self.is_listening:
                    try:
                        self.logger.debug("Listening...")
                        audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                        
                        # Recognize using Whisper
                        text = self.recognizer.recognize_whisper(audio).lower().strip()
                        
                        if text:
                            self.logger.debug(f"Recognized: {text}")
                            self._process_text(text)
                    
                    except sr.WaitTimeoutError:
                        continue
                    except sr.UnknownValueError:
                        self.logger.debug("Could not understand audio")
                    except Exception as e:
                        self.logger.error(f"Recognition error: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error in Whisper listen loop: {e}")
        finally:
            self.is_listening = False
    
    def _process_text(self, text: str):
        """Process recognized text with debug logging"""
        self.logger.info(f"[INFO] _process_text called with: {text}")
        # Check for stop command
        if self.stop_command in text:
            self.logger.info("[INFO] Stop command detected in _process_text")
            if self.on_command:
                self.logger.info("[INFO] Calling on_command callback")
                self.on_command('stop')
            # Disable session on stop command
            self.disable_session()
            return

        # Check for any wake word in text
        for wake_word in self.wake_words:
            if wake_word in text:
                self.logger.info(f"[INFO] Wake word '{wake_word}' detected in: {text}")
                # Extract text after wake word
                parts = text.split(wake_word, 1)
                if len(parts) > 1:
                    query = parts[1].strip()
                    self.logger.info(f"[INFO] Text after wake word: {query}")
                    # Enable session if user says "let's chat"
                    if "let's chat" in query:
                        self.enable_session()
                        if self.on_text:
                            self.logger.info("[INFO] Session enabled, calling on_text callback with query after wake word")
                            self.on_text(query)
                        return
                    # Otherwise, normal wake word behavior
                    if query and self.on_text:
                        self.logger.info("[INFO] Calling on_text callback with query after wake word")
                        self.on_text(query)
                return

        # If session is active, update last_session_time and send to chatbot
        if self.is_session_active():
            import time
            self.last_session_time = time.time()
            if self.on_text:
                self.logger.info("[INFO] Session active, calling on_text callback with full text")
                self.on_text(text)
            return

        # Otherwise, normal text callback (no session)
        if self.on_text:
            self.logger.info("[INFO] Calling on_text callback with full text (no wake word)")
            self.on_text(text)
    
    def recognize_once(self) -> Optional[str]:
        """Perform one-time voice recognition"""
        if self.engine == 'whisper' and SR_AVAILABLE:
            try:
                with sr.Microphone() as source:
                    self.logger.info("Listening...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    
                    text = self.recognizer.recognize_whisper(audio)
                    self.logger.info(f"Recognized: {text}")
                    return text
                    
            except Exception as e:
                self.logger.error(f"Recognition error: {e}")
                return None
        else:
            self.logger.warning("One-time recognition only supported with Whisper")
            return None
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_listening()
        self.audio.terminate()
