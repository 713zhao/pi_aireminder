import pyaudio

p = pyaudio.PyAudio()

print('Input Devices:')
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f"Index {i}: {info['name']} (Input)")

print('\nOutput Devices:')
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info['maxOutputChannels'] > 0:
        print(f"Index {i}: {info['name']} (Output)")
