#!/usr/bin/env python3
"""
Setup script for testing and development
Creates sample alarm sound if needed
"""
import os
import sys


def create_directory_structure():
    """Create necessary directories"""
    directories = [
        'logs',
        'assets',
        'models',
        'src'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created directory: {directory}")


def create_sample_alarm():
    """Create a simple beep alarm sound using pygame"""
    try:
        import pygame
        import numpy as np
        
        # Initialize pygame mixer
        pygame.mixer.init(frequency=22050, size=-16, channels=1)
        
        # Generate a simple beep tone
        sample_rate = 22050
        duration = 1.0  # seconds
        frequency = 800  # Hz
        
        # Create sine wave
        samples = int(sample_rate * duration)
        wave = np.sin(2 * np.pi * frequency * np.linspace(0, duration, samples))
        
        # Apply envelope to prevent clicking
        envelope = np.linspace(0, 1, samples // 10)
        wave[:len(envelope)] *= envelope
        wave[-len(envelope):] *= envelope[::-1]
        
        # Convert to 16-bit integers
        wave = (wave * 32767).astype(np.int16)
        
        # Create stereo sound
        stereo_wave = np.column_stack((wave, wave))
        
        # Save as WAV file using scipy or wave
        import wave
        import struct
        
        with wave.open('assets/alarm.wav', 'w') as wav_file:
            wav_file.setnchannels(2)  # stereo
            wav_file.setsampwidth(2)   # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(stereo_wave.tobytes())
        
        print("✓ Created sample alarm sound: assets/alarm.wav")
        
    except ImportError:
        print("⚠ Could not create alarm sound (pygame or numpy not installed)")
        print("  You can add your own alarm.wav file to the assets/ directory")


def check_dependencies():
    """Check if required dependencies are available"""
    required = {
        'yaml': 'PyYAML',
        'requests': 'requests',
        'pygame': 'pygame',
        'pyttsx3': 'pyttsx3',
        'pyaudio': 'pyaudio',
    }
    
    optional = {
        'vosk': 'vosk',
        'speech_recognition': 'SpeechRecognition',
        'openai': 'openai',
        'google.generativeai': 'google-generativeai',
    }
    
    print("\nChecking dependencies:")
    print("Required:")
    for module, package in required.items():
        try:
            __import__(module)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} - MISSING")
    
    print("\nOptional:")
    for module, package in optional.items():
        try:
            __import__(module)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  - {package} - not installed")


def display_next_steps():
    """Display next steps for setup"""
    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Install dependencies:")
    print("   pip install -r requirements.txt")
    print("\n2. Download Vosk model (for offline speech recognition):")
    print("   wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip")
    print("   unzip vosk-model-small-en-us-0.15.zip -d models/")
    print("\n3. Configure config.yaml:")
    print("   - Set your backend API URL")
    print("   - Add OpenAI or Gemini API key")
    print("   - Adjust settings as needed")
    print("\n4. Run the application:")
    print("   python src/main.py")
    print("\n5. Optional: Create a systemd service for auto-start")
    print("   See README.md for details")
    print("=" * 60)


def main():
    print("AI Reminder System - Setup")
    print("=" * 60)
    
    # Create directories
    create_directory_structure()
    
    # Create sample alarm
    create_sample_alarm()
    
    # Check dependencies
    check_dependencies()
    
    # Display next steps
    display_next_steps()


if __name__ == "__main__":
    main()
