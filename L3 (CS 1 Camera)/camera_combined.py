import socket
import subprocess
import sys
import time
import cv2
import numpy as np
import threading

output_file = '/Users/mlab/work/new3camera/output_video.mp4'
frame_width = 640  # 720p width
frame_height = 480  # 720p height
fps = 30.0
recording = False
running = True

def send_disconnect_signal():
    try:
        client_socket.sendall("DISCONNECT".encode())
    except:
        pass

def disconnect_and_shutdown():
    global running

    send_disconnect_signal()
    client_socket.close()
    running = False
    time.sleep(1)
    cv2.destroyWindow('Recording')
    subprocess.run(['osascript', '-e', 'tell application "Terminal" to close (every window whose name contains "mic_combined.py" or name contains "camera_combined.py")'])
    sys.exit(0)

def list_cameras():
    camera_list = []
    index = 0
    while True:
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                camera_list.append(f"Camera {index}")
            cap.release()
            time.sleep(0.5)
            index += 1
        else:
            cap.release()
            break
    return camera_list

def select_camera(cameras):
    if not cameras:
        disconnect_and_shutdown()
    #choice = 0  # Default to first camera for automation
    print("Available cameras:")
    for i, camera in enumerate(cameras):
        print(f"{i}: {camera}")
    choice = int(input("Select a camera by entering its number: "))
    if 0 <= choice < len(cameras):
        return choice
    else:
        print("Invalid choice. Shutting down...")
        disconnect_and_shutdown()

def socket_listener():
    global recording  # So we can modify the global recording flag
    
    while running:
        # Handle signals from the server
        try:
            signal = client_socket.recv(1024).decode()
            if signal == "1":
                recording = True
                print("Recording started...")
            elif signal == "2":
                recording = False
                print("Recording stopped.")
            elif signal == "3":
                print("Uploading video file")
            elif signal == "q":
                disconnect_and_shutdown()
            else:
                print("Received an unknown signal.")
        except socket.timeout:
            pass

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('localhost', 12341))
client_socket.settimeout(0.1)

available_cameras = list_cameras()
camera_choice = select_camera(available_cameras)

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_file, fourcc, fps, (frame_width, frame_height))
print(f"Trying to open camera with ID: {camera_choice}")
time.sleep(2)
selected_camera = cv2.VideoCapture(camera_choice)

if selected_camera.isOpened():
    print("Camera successfully opened")
else:
    print(f"Error: Could not open {available_cameras[camera_choice]}")
    disconnect_and_shutdown()

socket_thread = threading.Thread(target=socket_listener)
socket_thread.daemon = True  # Set the thread as a daemon so it will close when the main program exits
socket_thread.start()

# --- Main loop ---
while running:
    ret, frame = selected_camera.read()

    if not ret:
        print("Error: Failed to capture frame.")
        break

    frame = cv2.resize(frame, (frame_width, frame_height))
    frame = cv2.flip(frame, 1)
    cv2.imshow('Recording', frame)
    cv2.waitKey(1) # Necessary to open window

    if recording:
        out.write(frame)

out.release()
selected_camera.release()
cv2.destroyAllWindows()
