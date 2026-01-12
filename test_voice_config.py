"""
Test script to demonstrate voice configuration
"""
import win32com.client
import yaml

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

tts_config = config['tts']
voice_name = tts_config.get('voice_name')
rate = tts_config.get('rate', 150)
volume = tts_config.get('volume', 0.9)

print(f"Configuration:")
print(f"  Voice Name: {voice_name}")
print(f"  Rate: {rate}")
print(f"  Volume: {volume}")
print()

# Initialize speaker
speaker = win32com.client.Dispatch("SAPI.SpVoice")

# Set voice if specified
if voice_name:
    voices = speaker.GetVoices()
    found = False
    for i in range(voices.Count):
        voice = voices.Item(i)
        if voice_name in voice.GetDescription():
            speaker.Voice = voice
            print(f"✅ Using voice: {voice.GetDescription()}")
            found = True
            break
    if not found:
        print(f"⚠️  Voice '{voice_name}' not found, using default: {speaker.Voice.GetDescription()}")
else:
    print(f"Using default voice: {speaker.Voice.GetDescription()}")

# Configure settings
sapi_rate = int((rate - 150) / 15)
sapi_rate = max(-10, min(10, sapi_rate))
speaker.Rate = sapi_rate
speaker.Volume = int(volume * 100)

print(f"  SAPI Rate: {speaker.Rate}")
print(f"  SAPI Volume: {speaker.Volume}")
print()

# Test speech
test_text = "Hello! This is a test of the text to speech voice configuration."
print(f"Speaking: '{test_text}'")
speaker.Speak(test_text)
print("✅ Done!")
