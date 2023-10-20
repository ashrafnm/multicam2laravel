import socket
import threading
import subprocess
import time
import cv2
import pyaudio
import os
import datetime

expected_clients = 0
connected_clients = []
client_threads = []
server_running = True

# Function to run a script in a new Terminal window
def run_script_in_terminal(script_name):
    command = f"""
    tell application "Terminal"
        do script "python3 /Users/mlab/work/new3camera/{script_name}"
    end tell
    """
    subprocess.Popen(['osascript', '-e', command])

# Define the communication logic
def send_signal_to_all(signal_code):
    for client_socket in connected_clients:
        client_socket.send(str(signal_code).encode())

# Function to handle each client in a separate thread
def handle_client(client_socket):
    print(f"Client connected from {client_socket.getpeername()}")
    
    # Add the client socket to the list of connected clients
    connected_clients.append(client_socket)

    if len(connected_clients) == expected_clients:
        start_command_loop()

    while True:
        signal = client_socket.recv(1024).decode()
        if signal == "DISCONNECT":
            print(f"Client {client_socket.getpeername()} has disconnected.")
            connected_clients.remove(client_socket)
            client_socket.close()
            break

def start_command_loop():
    global server_running
    try:
        while True:
            command = input("Enter command (1 for start, 2 for stop, 3 for upload, q to quit): ")
            
            if command in ["1", "2", "3"]:
                send_signal_to_all(command)
            elif command == "q":
                send_signal_to_all("q")  
                server_running = False  
                break
            else:
                print("Invalid command. Please enter 1 (start), 2 (stop), 3 (upload), or q (quit).")
    except KeyboardInterrupt:
        pass

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

# Function to list available microphones with portacapture keyword
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

# Get the number of connected devices
def get_connected_devices():
    # Subtract 1 to ignore the native camera
    camera_count = len(list_cameras()) - 1
    microphone_count = len(list_microphones())
    return microphone_count, camera_count,camera_count + microphone_count

microphone_count, camera_count,expected_clients = get_connected_devices()
print(f"Expecting {expected_clients} clients.")

# Create a new directory with folder format "recording_YYYYMMDDHHMM"
# timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
# folder_name = f"recording_{timestamp}"

# try:
#     os.mkdir(folder_name)
#     print(f"Created directory: {folder_name}")
# except FileExistsError:
#     print(f"Directory {folder_name} already exists.")

# Create a server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost', 12341))
server_socket.listen(expected_clients)
server_socket.settimeout(1)

print("Server is listening for clients...")

# Wait for a few seconds to ensure the clients have started
time.sleep(1)

for _ in range(microphone_count):
    run_script_in_terminal('mic_combined.py')

for _ in range(camera_count):
    run_script_in_terminal('camera_combined.py')

try:
    while server_running:
        try:
            # Accept a client connection
            client_socket, client_address = server_socket.accept()
            print(f"Accepted connection from {client_address}")
            
            # Create a thread to handle the client
            client_thread = threading.Thread(target=handle_client, args=(client_socket,))
            client_thread.start()
            
            # Add the client thread to the list
            client_threads.append(client_thread)
        except socket.timeout:
            # Just a timeout, continue checking server_running
            pass
except KeyboardInterrupt:
    print("Server is quitting...")
    send_signal_to_all("q")

# Wait for all client threads to finish
for thread in client_threads:
    thread.join()

# Close the server socket
server_socket.close()
