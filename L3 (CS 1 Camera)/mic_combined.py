import socket
import subprocess
import sys
import pyaudio
import wave
import threading
import os

device_index = None
recording_thread = None

def send_disconnect_signal():
    try:
        client_socket.sendall("DISCONNECT".encode())
    except:
        pass

def disconnect_and_shutdown():
    print("Client is disconnecting and shutting down...")
    send_disconnect_signal()
    client_socket.close()
    subprocess.run(['osascript', '-e', 'tell application "Terminal" to close (every window whose name contains "mic_combined.py" or name contains "camera_combined.py")'])
    sys.exit(0)

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

def start_audio_recording():
    global recording_thread
    if device_index is None:
        return

    output_file = "/Users/mlab/work/new3camera/recorded_audio.wav"
    stop_event.clear()
    recording_thread = threading.Thread(target=record_audio, args=(device_index, output_file))
    recording_thread.start()

def stop_audio_recording():
    global recording_thread
    if recording_thread is None:
        print("Recording hasn't started!")
        return
    stop_event.set()
    recording_thread.join()


def record_audio(device_index, output_file, sample_rate=44100, channels=1):
    audio = pyaudio.PyAudio()
    print("Enter record audio")
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=channels,
        rate=sample_rate,
        input=True,
        input_device_index=device_index,
        frames_per_buffer=1024
    )

    frames = []
    while not stop_event.is_set():
        data = stream.read(1024)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    audio.terminate()

    try:
        with wave.open(output_file, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(sample_rate)
            wf.writeframes(b''.join(frames))
            print(f"Audio saved to {output_file}")
    except Exception as e:
        print("Error while saving audio:", e)

print("Current working directory:", os.getcwd())
# Create a client socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('localhost', 12341))

print("Connected to server")

devices = list_input_devices()
for i, device in enumerate(devices):
        print(f"{i}: {device['name']} (Sample Rate: {device['rate']})")
# if devices:
#     device_index = devices[0]['index']  # Just select the first one for simplicity
#     stop_event = threading.Event()

for device in devices:
    if "portacapture" in device['name'].lower():
        device_index = device['index']
        print("Selected device", device_index)
        break

if device_index is None:
    print("No device with keyword 'portacapture' found!")
else:
    stop_event = threading.Event()

while True:
    try:
        # Receive and process signals
        signal = client_socket.recv(1024).decode()
        
        if signal == "1":
            print("Start audio recording")
            start_audio_recording()
        elif signal == "2":
            print("Stop audio recording")
            stop_audio_recording()
        elif signal == "3":
            print("Uploading audio file")
        elif signal == "q":
            disconnect_and_shutdown()
        else:
            print("Received an unknown signal.")
    
    except KeyboardInterrupt:
        disconnect_and_shutdown()

client_socket.close()
