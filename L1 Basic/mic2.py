import pyaudio
import wave
import threading

# Function to list available input devices
def list_input_devices():
    audio = pyaudio.PyAudio()
    info = audio.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')

    devices = []

    for i in range(numdevices):
        device = audio.get_device_info_by_host_api_device_index(0, i)
        if device.get('maxInputChannels') > 0:
            devices.append({
                'index': i,
                'name': device.get('name'),
                'rate': int(device.get('defaultSampleRate'))
            })

    return devices

# Function to select an input device
def select_input_device(devices):
    if not devices:
        print("No input devices found.")
        return None
    print("Available input devices:")
    for i, device in enumerate(devices):
        print(f"{i}: {device['name']} (Sample Rate: {device['rate']})")

    choice = int(input("Select the microphone (enter its number): "))
    if 0 <= choice < len(devices):
        return devices[choice]['index']
    else:
        print("Invalid choice.")
        return None

# Function to start audio recording
def start_audio_recording(device_index, output_file, sample_rate=44100, channels=1):
    audio = pyaudio.PyAudio()

    stream = audio.open(
        format=pyaudio.paInt16,
        channels=channels,
        rate=sample_rate,
        input=True,
        input_device_index=device_index,
        frames_per_buffer=1024
    )

    print("Recording audio... Press 'q' to stop.")

    frames = []
    recording = True

    while recording:
        data = stream.read(1024)
        frames.append(data)
        if stop_event.is_set():
            recording = False

    stream.stop_stream()
    stream.close()
    audio.terminate()

    with wave.open(output_file, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(frames))
        print(f"Audio saved to {output_file}")

# Function to stop audio recording
def stop_audio_recording():
    stop_event.set()

if __name__ == "__main__":
    devices = list_input_devices()
    if not devices:
        print("No input devices found.")
    else:
        device_index = select_input_device(devices)
        if device_index is not None:
            output_file = "recorded_audio.wav"  # Change this to your desired output file
            stop_event = threading.Event()
            recording_started = False  # Flag to track whether recording has started
            print("Press 's' to start recording, 'q' to stop: ")
            
            while True:
                user_input = input()
                if user_input == 's':
                    if not recording_started:
                        stop_event.clear()
                        recording_thread = threading.Thread(target=start_audio_recording, args=(device_index, output_file))
                        recording_thread.start()
                        recording_started = True
                    else:
                        print("Recording already started.")
                elif user_input == 'q':
                    if recording_started:
                        stop_audio_recording()
                        recording_thread.join()
                        print("Recording stopped.")
                    else:
                        print("Recording not started.")
                    break
                else:
                    print("Invalid input.")

