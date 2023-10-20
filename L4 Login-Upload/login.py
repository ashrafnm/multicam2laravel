import tkinter as tk
from tkinter import messagebox
import subprocess
import requests 

def on_login():
    email = entry_email.get()
    password = entry_password.get()
    
    # Define the URL and payload
    url = 'http://150.7.136.76:80/api/login' 
    payload = {'email': email, 'password': password}
    
    # Send POST request to server
    response = requests.post(url, data=payload)
    response_data = response.json()
    
    # Check response
    if response.status_code == 200 and response.json()['status'] == 'success':
        root.destroy()
        subprocess.run(["python3", "gui.py"])
    else:
        error_message = response_data.get('message', 'Login failed')
        print("Server Response:", error_message)  # Print message to console
        messagebox.showerror("Login info", error_message)

# Create the main window
root = tk.Tk()
root.title("Login Window")

# Create & Place widgets
label_email = tk.Label(root, text="Email:")
label_email.pack(pady=5)

entry_email = tk.Entry(root, width=30)
entry_email.pack(pady=5, padx=15)

label_password = tk.Label(root, text="Password:")
label_password.pack(pady=5)

entry_password = tk.Entry(root, width=30, show="*")
entry_password.pack(pady=5, padx=15)

button_login = tk.Button(root, text="Login", command=on_login)
button_login.pack(pady=15)

# Start the GUI event loop
root.mainloop()
