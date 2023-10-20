import shutil
import socket
import subprocess
import sys
import time
import cv2
import numpy as np
import threading
import atexit

folder_name = sys.argv[1]
camera_id = int(sys.argv[2])
port_number = int(sys.argv[3])
output_file = f'/Users/mlab/work/new3camera/{folder_name}/output_video_{camera_id}.mp4'
frame_width = 1280  # 720p width
frame_height = 720  # 720p height
fps = 30.0
recording = False
running = True

def send_disconnect_signal():
    try:
        client_socket.sendall("DISCONNECT".encode())
    except:
        pass

def disconnect_and_shutdown():
    global running, folder_name, camera_id

    send_disconnect_signal()
    client_socket.close()
    running = False
    time.sleep(1)
    cv2.destroyWindow('Recording')
    subprocess.run(['osascript', '-e', f'tell application "Terminal" to close (every window whose name contains "mic_combined.py" or name contains "camera_combined.py {folder_name} {camera_id}")'])
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
                if out is not None:
                    out.release()

                convert_video(output_file)
            elif signal == "3":
                print("Uploading video file")
            elif signal == "q":
                print("Server is shutting down...")
                disconnect_and_shutdown()
            else:
                print("Received an unknown signal.")
        except socket.timeout:
            pass

def write_frame(frame):
    global out, recording, output_file
    if recording:
        if out is None:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_file, fourcc, fps, (frame_width, frame_height))
        out.write(frame)
    elif out is not None:
        out.release()
        out = None  # Reset the writer, so it is re-initialized on next record

def clean_up():
    global out, selected_camera
    if out is not None:
        out.release()
    selected_camera.release()
    cv2.destroyAllWindows()

def convert_video(input_file):
    # Determine the new output file path
    temp_output_file = input_file.replace('.mp4', '_temp.mp4')
    
    try:
        subprocess.run([
            'ffmpeg', '-y', '-i', input_file, '-c:v', 'libx264', '-c:a', 'aac',
            '-strict', 'experimental', temp_output_file
        ], check=True)
        print(f"Video converted successfully: {temp_output_file}")

        # Replace the original file with the converted file
        shutil.move(temp_output_file, input_file)
        print(f"Original video replaced with converted video: {input_file}")

    except subprocess.CalledProcessError:
        print("Error during video conversion.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    
    return input_file


client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('localhost', port_number))
client_socket.settimeout(0.1)

available_cameras = list_cameras()
if len(sys.argv) > 1:
    camera_choice = int(sys.argv[2])
else:
    camera_choice = select_camera(available_cameras)

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_file, fourcc, fps, (frame_width, frame_height))
print(f"Trying to open camera with ID: {camera_choice}")
time.sleep(2)
selected_camera = cv2.VideoCapture(camera_choice)

atexit.register(clean_up)

if selected_camera.isOpened():
    print("Camera successfully opened")
else:
    print(f"Error: Could not open {available_cameras[camera_choice]}")
    disconnect_and_shutdown()

socket_thread = threading.Thread(target=socket_listener)
socket_thread.daemon = True  
socket_thread.start()

# --- Main loop ---
while running:
    ret, frame = selected_camera.read()

    if not ret:
        print("Error: Failed to capture frame.")
        break

    frame = cv2.resize(frame, (frame_width, frame_height))
    frame = cv2.flip(frame, 1)
    cv2.imshow(f'Recording Camera {camera_choice}', frame)
    cv2.waitKey(1) # Necessary to open window

    write_frame(frame)
