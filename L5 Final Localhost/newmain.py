import sys
import time
import tkinter as tk
import threading
import socket
import datetime
import os
import cv2
import pyaudio
import subprocess
import requests
import shutil
from tqdm import tqdm

def run_script_in_terminal(script_name, folder_name, camera_id=None):
    if camera_id is not None:
        command = f"""
        tell application "Terminal"
            do script "python3 /Users/mlab/work/new3camera/{script_name} {folder_name} {camera_id}"
        end tell
        """
    else:
        command = f"""
        tell application "Terminal"
            do script "python3 /Users/mlab/work/new3camera/{script_name} {folder_name}"
        end tell
        """
    subprocess.Popen(['osascript', '-e', command])

def list_cameras():
    camera_list = []
    for i in range(3):  # Increase range if you expect more than 10 cameras
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                camera_list.append(i)  # append camera index
            cap.release()
    return camera_list

def list_microphones():
    audio = pyaudio.PyAudio()
    num_devices = audio.get_device_count()

    devices = []

    for i in range(num_devices):
        device_info = audio.get_device_info_by_index(i)
        if device_info['maxInputChannels'] > 0 and 'portacapture' in device_info['name'].lower():
            devices.append({
                'index': i,
                'name': device_info['name'],
                'rate': int(device_info['defaultSampleRate'])
            })

    return devices

class ServerController:
    def __init__(self, ui_callback=None):
        self.connected_clients = []
        self.client_threads = []
        self.server_running = True
        self.clients_lock = threading.Lock()
        self.ui_callback = ui_callback

        # Get connected devices and set expected clients
        microphone_count, camera_count, self.expected_clients = self.get_connected_devices()
        print(f"Expected clients (based on connected devices): {self.expected_clients}")
        
        #Create a new directory with folder format "recording_YYYYMMDDHHMM"
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
        self.folder_name = f"{timestamp}"

        try:
            os.mkdir(self.folder_name)
            print(f"Created directory: {self.folder_name}")
        except FileExistsError:
            print(f"Directory {self.folder_name} already exists.")

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('localhost', 12348))
        self.server_socket.listen(5)  # arbitrary number of expected_clients
        self.server_socket.settimeout(1)
        
        time.sleep(1)

        for _ in range(microphone_count):
            run_script_in_terminal('mic_combined.py', self.folder_name)

        available_cameras = list_cameras()

        for cam_id in available_cameras:
            run_script_in_terminal('camera_combined.py', self.folder_name, cam_id)

    def get_connected_devices(self):
        camera_count = len(list_cameras())
        microphone_count = len(list_microphones())
        return microphone_count, camera_count, camera_count + microphone_count

    def send_signal_to_all(self, signal_code):
        for client_socket in self.connected_clients:
            client_socket.send(str(signal_code).encode())

    def handle_client(self, client_socket):
        print(f"Client connected from {client_socket.getpeername()}")

        with self.clients_lock:
            self.connected_clients.append(client_socket)

        if len(self.connected_clients) == self.expected_clients:
            self.server_socket.close()
            if self.ui_callback is not None:
                self.ui_callback("All clients connected")

        while True:
            signal = client_socket.recv(1024).decode()
            if signal == "DISCONNECT":
                print(f"Client {client_socket.getpeername()} has disconnected.")
                
                with self.clients_lock:
                    self.connected_clients.remove(client_socket)
                    if not self.connected_clients:
                        print("No connected clients")
                        self.server_running = False
                
                client_socket.close()
                break

    def start_server_listening(self):
        try:
            while True:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    print(f"Accepted connection from {client_address}")

                    with self.clients_lock:
                        if self.server_running:
                            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True)
                            client_thread.start()
                            self.client_threads.append(client_thread)
                except socket.timeout:
                    pass
                except OSError:
                    break
        except KeyboardInterrupt:
            print("Server is quitting...")
            self.send_signal_to_all("q")
    
    def shutdown_server(self):
        # Send a signal to shut down all client threads...
        self.send_signal_to_all("q")
        
        # Ensure all threads are finished
        for thread in self.client_threads:
            thread.join()  # wait for the thread to finish

        # Close the server socket if it is still open
        if self.server_socket:
            self.server_socket.close()

        print("Server shutdown complete.")

class ControlServerUI(tk.Tk):
    def __init__(self, server_controller):
        super().__init__()
        self.server_controller = server_controller
        self.title("Server Control")
        self.geometry("300x200")
        self.create_widgets()

    def create_widgets(self):
        self.start_button = tk.Button(self, text="Start", command=self.start_server)
        self.start_button.pack(pady=5)

        self.stop_button = tk.Button(self, text="Stop", command=self.stop_server)
        self.stop_button.pack(pady=5)

        self.upload_button = tk.Button(self, text="Upload", command=self.upload_data)
        self.upload_button.pack(pady=5)

        self.quit_button = tk.Button(self, text="Quit", command=self.quit_server)
        self.quit_button.pack(pady=5)

        self.status_label = tk.Label(self, text="Awaiting client connections...")
        self.status_label.pack(pady=5)

    def start_server(self):
        self.server_controller.send_signal_to_all("1")

    def stop_server(self):
        self.server_controller.send_signal_to_all("2")

    def upload_data(self):
        self.server_controller.send_signal_to_all("3")
        
        practice_date = datetime.datetime.now().strftime("%Y-%m-%d")
        recording_start_time = datetime.datetime.now().strftime("%H:%M")
        score_id, score_title, score_user_id = sys.argv[1], sys.argv[2], sys.argv[3]

        recording_folder_path = os.path.join(os.getcwd(), self.server_controller.folder_name)

        files = []
        for filename in os.listdir(recording_folder_path):
            # Ignore hidden files (those starting with a dot)
            if filename.startswith('.'):
                continue

            file_path = os.path.join(recording_folder_path, filename)
            if os.path.isfile(file_path):
                with open(file_path, 'rb') as file:
                    files.append(('video[]', (filename, file.read())))

        payload = {
            'title': score_title,
            'user_id': score_user_id,
            'practice_date': practice_date,
            'time': recording_start_time,
            'score_id': score_id,
        }

        upload_thread = threading.Thread(target=self.upload_thread, args=(payload, files))
        upload_thread.start()

        # Show a loading bar/spinner until the upload is done.
        print("Uploading data...")
        for _ in tqdm(range(100), position=0, leave=True):
            time.sleep(0.1)  # Sleep while the upload_thread does its job.
            if not upload_thread.is_alive():
                break  # If upload is done, exit the loop.
        
        # Optionally wait for the upload thread to finish, if it isn't done yet.
        upload_thread.join()
    
    def upload_thread(self, payload, files):
        upload_url = "http://150.7.136.76:80/api/upload-python"
        response = requests.post(upload_url, data=payload, files=files)

        if response.status_code == 200:
            print("\nData uploaded successfully")
            print('HTTP Status Code:', response.status_code)
            print('HTTP Reason Phrase:', response.reason)
            print('Response Text:', response.text)
        else:
            print(f"\nFailed to upload data: {response.text}")

    def quit_server(self):
        self.server_controller.shutdown_server()
        self.destroy()
    
    def update_status(self, new_status):
        self.status_label.config(text=new_status)

def main(score_id, score_title, score_user_id):
    # Your script logic goes here
    print(f"Running with score id: {score_id}, title: {score_title}, user_id: {score_user_id}")

# Main execution
def ui_update_status_callback(new_status):
    app.update_status(new_status)

if __name__ == "__main__":
    # Check if the right number of parameters are provided
    if len(sys.argv) != 4:
        print("Usage: newmain.py <score_id> <score_title> <score_user_id>")
    else:
        score_id, score_title, score_user_id = sys.argv[1], sys.argv[2], sys.argv[3]
        main(score_id, score_title, score_user_id)
    
    server_controller = ServerController(ui_callback=ui_update_status_callback)

    # Starting server listener in a new thread
    server_thread = threading.Thread(target=server_controller.start_server_listening)
    server_thread.start()

    # Starting GUI in the main thread
    app = ControlServerUI(server_controller)
    app.mainloop()

