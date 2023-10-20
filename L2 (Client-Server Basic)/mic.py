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
        pass

def disconnect_and_shutdown():
    print("Client is disconnecting and shutting down...")
    send_disconnect_signal()
    client_socket.close()
    subprocess.run(['osascript', '-e', 'tell application "Terminal" to close (every window whose name contains "mic.py" or name contains "camera.py")'])
    sys.exit(0)

while True:
    try:
        # Receive and process signals
        signal = client_socket.recv(1024).decode()
        
        if signal == "1":
            print("Start audio recording")
        elif signal == "2":
            print("Stop audio recording")
        elif signal == "3":
            print("Uploading audio file")
        elif signal == "q":
            disconnect_and_shutdown()  # Disconnect and shut down on "q" signal
        else:
            print("Received an unknown signal.")
    
    except KeyboardInterrupt:
        disconnect_and_shutdown()  # Disconnect and shut down on Ctrl+C

# Close the socket (this should not be reached in normal execution)
client_socket.close()
