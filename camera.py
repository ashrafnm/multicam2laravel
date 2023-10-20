import shutil
import socket
import subprocess
import sys
import time
import cv2
import numpy as np
import threading
import atexit
import os

class VideoClient:
    def __init__(self, folder_name, camera_id, port_number):
        home_dir = os.path.expanduser("~")

        self.folder_name = folder_name
        self.camera_id = camera_id
        self.port_number = port_number
        self.output_file = os.path.join(home_dir, 'work', 'new3camera', folder_name, f'output_video_{camera_id}.mp4')
        self.frame_width = 1280
        self.frame_height = 720
        self.fps = 29.6
        self.recording = False
        self.running = True
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.settimeout(0.1)
        self.out = None
        self.selected_camera = None

    def start(self):
        self.client_socket.connect(('localhost', self.port_number))
        available_cameras = self.list_cameras()
        self.selected_camera = cv2.VideoCapture(self.camera_id)

        if not self.selected_camera.isOpened():
            print(f"Error: Could not open {available_cameras[self.camera_id]}")
            self.disconnect_and_shutdown()

        atexit.register(self.clean_up)
        socket_thread = threading.Thread(target=self.socket_listener)
        socket_thread.daemon = True
        socket_thread.start()

        while self.running:
            ret, frame = self.selected_camera.read()
            if not ret:
                print("Error: Failed to capture frame.")
                break

            frame = cv2.resize(frame, (self.frame_width, self.frame_height))
            #frame = cv2.flip(frame, 0)
            cv2.imshow(f'Recording Camera {self.camera_id}', frame)
            cv2.waitKey(1)
            self.write_frame(frame)

    def send_disconnect_signal(self):
        try:
            self.client_socket.sendall("DISCONNECT".encode())
        except:
            pass

    def disconnect_and_shutdown(self):
        self.send_disconnect_signal()
        self.client_socket.close()
        self.running = False
        time.sleep(1)
        cv2.destroyWindow('Recording')
        subprocess.run(['osascript', '-e', f'tell application "Terminal" to close (every window whose name contains "mic_combined.py" or name contains "camera_combined.py {self.folder_name} {self.camera_id}")'])
        sys.exit(0)

    def list_cameras(self):
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

    def socket_listener(self):
        while self.running:
            try:
                signal = self.client_socket.recv(1024).decode()
                if signal == "1":
                    self.recording = True
                    print("Recording started...")
                elif signal == "2":
                    self.recording = False
                    print("Recording stopped.")
                    if self.out is not None:
                        self.out.release()

                    self.convert_video(self.output_file)
                    self.client_socket.send("UPLOAD_READY".encode())
                elif signal == "3":
                    print("Uploading video file")
                elif signal == "q":
                    print("Server is shutting down...")
                    self.disconnect_and_shutdown()
                else:
                    print("Received an unknown signal.")
            except socket.timeout:
                pass

    def write_frame(self, frame):
        if self.recording:
            if self.out is None:
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                self.out = cv2.VideoWriter(self.output_file, fourcc, self.fps, (self.frame_width, self.frame_height))
            self.out.write(frame)
        elif self.out is not None:
            self.out.release()
            self.out = None

    def clean_up(self):
        if self.out is not None:
            self.out.release()
        if self.selected_camera is not None:
            self.selected_camera.release()
        cv2.destroyAllWindows()

    def convert_video(self, input_file):
        temp_output_file = input_file.replace('.mp4', '_temp.mp4')
        try:
            subprocess.run([
                'ffmpeg', '-y', '-i', input_file, '-c:v', 'libx264', '-c:a', 'aac',
                '-strict', 'experimental', temp_output_file
            ], check=True)
            print(f"Video converted successfully: {temp_output_file}")
            shutil.move(temp_output_file, input_file)
            print(f"Original video replaced with converted video: {input_file}")
        except subprocess.CalledProcessError:
            print("Error during video conversion.")
        except Exception as e:
            print(f"An error occurred: {str(e)}")

def main(args):
    client = VideoClient(args['folder_name'], args['camera_id'], args['port_number'])
    client.start()

if __name__ == "__main__":
    folder_name = sys.argv[1]
    camera_id = int(sys.argv[3])
    port_number = int(sys.argv[2])
    main({'folder_name': folder_name, 'camera_id': camera_id, 'port_number': port_number})
