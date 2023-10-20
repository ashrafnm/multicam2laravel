import socket
import subprocess
import sys

# Create a client socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('localhost', 12341))

print("Connected to server")

def send_disconnect_signal():
    try:
        client_socket.sendall("DISCONNECT".encode())
    except:
        # It's a last effort message, so if it fails, just move on
        pass


# Function to gracefully disconnect and shut down the client
def disconnect_and_shutdown():
    print("Client is disconnecting and shutting down...")
    send_disconnect_signal()
    client_socket.close()
    # Execute a command to close the terminal window (macOS-specific)
    subprocess.run(['osascript', '-e', 'tell application "Terminal" to close (every window whose name contains "mic.py" or name contains "camera.py")'])
    sys.exit(0)

while True:
    try:
        # Receive and process signals
        signal = client_socket.recv(1024).decode()
        
        if signal == "1":
            print("Start video recording")
        elif signal == "2":
            print("Stop video recording")
        elif signal == "3":
            print("Uploading video file")
        elif signal == "q":
            disconnect_and_shutdown()  # Disconnect and shut down on "q" signal
        else:
            print("Received an unknown signal.")
    
    except KeyboardInterrupt:
        disconnect_and_shutdown()  # Disconnect and shut down on Ctrl+C

# Close the socket
client_socket.close()
