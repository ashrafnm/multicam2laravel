import socket
import subprocess
import sys
import pyaudio
import wave
import threading
import os
import argparse

class AudioClient:
    def __init__(self, folder_name, port_number):
        self.folder_name = folder_name
        self.port_number = port_number
        self.device_index = None
        self.recording_thread = None
        self.stop_event = threading.Event()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        self.connect_to_server()
        self.list_and_select_device()
        self.listen_for_signals()

    def connect_to_server(self):
        print("Current working directory:", os.getcwd())
        self.client_socket.connect(('localhost', self.port_number))
        print("Connected to server")

    def list_and_select_device(self):
        devices = self.list_input_devices()
        for device in devices:
            if "portacapture" in device['name'].lower():
                self.device_index = device['index']
                print("Selected device", self.device_index)
                return
        print("No device with keyword 'portacapture' found!")

    def listen_for_signals(self):
        while True:
            try:
                signal = self.client_socket.recv(1024).decode()

                if signal == "1":
                    self.start_audio_recording()
                elif signal == "2":
                    self.stop_audio_recording()
                    self.client_socket.send("AUDIO_READY".encode())
                elif signal == "3":
                    print("Uploading audio file")
                elif signal == "q":
                    self.disconnect_and_shutdown()
                else:
                    print("Received an unknown signal.")

            except KeyboardInterrupt:
                self.disconnect_and_shutdown()

    def start_audio_recording(self):
        if self.device_index is None:
            return

        home_dir = os.path.expanduser("~")
        output_file = os.path.join(home_dir, 'work', 'new3camera', self.folder_name, 'recorded_audio.wav')
        print(output_file)
        self.stop_event.clear()
        self.recording_thread = threading.Thread(target=self.record_audio, args=(self.device_index, output_file))
        self.recording_thread.start()

    def stop_audio_recording(self):
        if self.recording_thread is None:
            print("Recording hasn't started!")
            return
        self.stop_event.set()
        self.recording_thread.join()

    def record_audio(self, device_index, output_file, sample_rate=44100, channels=1):
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
        while not self.stop_event.is_set():
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

    def send_disconnect_signal(self):
        try:
            self.client_socket.sendall("DISCONNECT".encode())
        except:
            pass

    def disconnect_and_shutdown(self):
        print("Client is disconnecting and shutting down...")
        self.send_disconnect_signal()
        self.client_socket.close()
        subprocess.run(['osascript', '-e', 'tell application "Terminal" to close (every window whose name contains "mic_combined.py" or name contains "camera_combined.py")'])
        sys.exit(0)

    def list_input_devices(self):
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


def main(args):
    client = AudioClient(args.folder_name, args.port_number)
    client.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audio Recording Client")
    parser.add_argument('folder_name', help="The name of the folder to save audio recordings.")
    parser.add_argument('port_number', type=int, help="The server port number to connect to.")
    args = parser.parse_args()

    main(args)
