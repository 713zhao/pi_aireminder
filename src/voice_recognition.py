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
        
        # Initialize recognizer
        self.engine = self.config.get('engine', 'vosk').lower()
        self.recognizer = None
        self.model = None
        
        if self.engine == 'vosk':
            self._init_vosk()
        elif self.engine == 'whisper':
            self._init_whisper()
        
        # Audio configuration
        self.sample_rate = self.config.get('sample_rate', 16000)
        self.device_index = self.config.get('device_index')
        
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
        
        # Wake word and commands
        self.wake_word = self.config.get('wake_word', 'assistant').lower()
        self.stop_command = self.config.get('stop_command', 'stop').lower()
        
    def _init_vosk(self):
        """Initialize Vosk speech recognition"""
        if not VOSK_AVAILABLE:
            self.logger.error("Vosk is not installed")
            return
        
        model_path = self.config.get('model_path')
        if not model_path or not os.path.exists(model_path):
            self.logger.error(f"Vosk model not found: {model_path}")
            return
        
        try:
            self.model = Model(model_path)
            self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
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
        """Vosk listening loop"""
        try:
            while self.is_listening and self.stream:
                data = self.stream.read(4000, exception_on_overflow=False)
                
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get('text', '').lower().strip()
                    
                    if text:
                        self.logger.debug(f"Recognized: {text}")
                        self._process_text(text)
                
        except Exception as e:
            self.logger.error(f"Error in Vosk listen loop: {e}")
        finally:
            self.is_listening = False
    
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
        """Process recognized text"""
        # Check for stop command
        if self.stop_command in text:
            self.logger.info("Stop command detected")
            if self.on_command:
                self.on_command('stop')
            return
        
        # Check for wake word
        if self.wake_word in text:
            self.logger.info("Wake word detected")
            # Extract text after wake word
            parts = text.split(self.wake_word, 1)
            if len(parts) > 1:
                query = parts[1].strip()
                if query and self.on_text:
                    self.on_text(query)
            return
        
        # General text callback
        if self.on_text:
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
