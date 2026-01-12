"""
Script to list available Windows SAPI voices
"""
import win32com.client

speaker = win32com.client.Dispatch("SAPI.SpVoice")
voices = speaker.GetVoices()

print("Available Windows SAPI Voices:")
print("=" * 60)
for i in range(voices.Count):
    voice = voices.Item(i)
    print(f"\nVoice {i}:")
    print(f"  Name: {voice.GetDescription()}")
    print(f"  ID: {voice.Id}")
    
print("\n" + "=" * 60)
print(f"\nCurrent voice: {speaker.Voice.GetDescription()}")
print(f"Current rate: {speaker.Rate} (range: -10 to 10)")
print(f"Current volume: {speaker.Volume} (range: 0 to 100)")
