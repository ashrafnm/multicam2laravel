import cv2
import numpy as np

# Function to list available cameras
def list_cameras():
    camera_list = []
    for i in range(3):  # Assume up to 3 cameras
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                camera_list.append(f"Camera {i}")
        cap.release()
    return camera_list

# Function to select a camera
def select_camera(cameras):
    if not cameras:
        print("No cameras found.")
        return None
    print("Available cameras:")
    for i, camera in enumerate(cameras):
        print(f"{i}: {camera}")
    choice = int(input("Select a camera by entering its number: "))
    if 0 <= choice < len(cameras):
        return choice
    else:
        print("Invalid choice.")
        return None

# Video settings
output_file = 'output_video.mp4'
frame_width = 1280  # 720p width
frame_height = 720  # 720p height
fps = 30.0

# List available cameras and choose one
available_cameras = list_cameras()
camera_choice = select_camera(available_cameras)
if camera_choice is None:
    exit()

# Initialize the video writer
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Specify the codec
out = cv2.VideoWriter(output_file, fourcc, fps, (frame_width, frame_height))

# Initialize the selected webcam
selected_camera = cv2.VideoCapture(camera_choice)

if not selected_camera.isOpened():
    print(f"Error: Could not open {available_cameras[camera_choice]}")
    exit()

recording = False  # Flag to indicate recording state

while True:
    ret, frame = selected_camera.read()  # Read a frame from the selected camera

    if not ret:
        print("Error: Failed to capture frame.")
        break

    # Resize the frame to 720p
    frame = cv2.resize(frame, (frame_width, frame_height))

    # Mirror the frame horizontally
    frame = cv2.flip(frame, 1)

    # Display the frame (optional)
    cv2.imshow('Recording', frame)

    # Check for key presses
    key = cv2.waitKey(1)
    
    # Press 's' to start/stop recording
    if key == ord('s'):
        recording = not recording
        if recording:
            print("Recording started...")
        else:
            print("Recording stopped.")
    
    # Write the frame to the video file if recording is active
    if recording:
        out.write(frame)

    # Press 'q' to quit
    if key == ord('q'):
        break

# Release the video writer and selected camera
out.release()
selected_camera.release()

# Close all OpenCV windows
cv2.destroyAllWindows()
