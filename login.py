import os
import signal
import tkinter as tk
from tkinter import messagebox, Toplevel, Listbox, SINGLE
import requests 
import subprocess
import sys

class LoginApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Login Window")
        
        label_email = tk.Label(self, text="Email:")
        label_email.pack(pady=5)

        self.entry_email = tk.Entry(self, width=30)
        self.entry_email.pack(pady=5, padx=15)

        label_password = tk.Label(self, text="Password:")
        label_password.pack(pady=5)

        self.entry_password = tk.Entry(self, width=30, show="*")
        self.entry_password.pack(pady=5, padx=15)

        button_login = tk.Button(self, text="Login", command=self.on_login)
        button_login.pack(pady=15)

    def on_login(self):
        email = self.entry_email.get()
        password = self.entry_password.get()
        url = 'https://mdev.jt.u-tokai.ac.jp/api/login'
        payload = {'email': email, 'password': password}

        try:
            response = requests.post(url, data=payload)
            response_data = response.json()
        except requests.RequestException as e:
            messagebox.showerror("Network Error", str(e))
            return

        if response.status_code == 200 and response_data['status'] == 'success':
            scores = {score['id']: {'title': score['title'], 'user_id': score['user_id']} for score in response_data.get('scores', [])}
            self.destroy()  
            app = ServerApp(scores)
            app.mainloop()
        else:
            error_message = response.json().get('message', 'Login failed')
            messagebox.showerror("Login info", error_message)

class ServerApp(tk.Tk):
    def __init__(self, scores=None):
        super().__init__()

        if scores is None:
            scores = []

        self.selected_score = None
        self.scores = scores
        self.title("Server App")
        self.geometry("400x150")  
        
        button_frame = tk.Frame(self)
        button_frame.pack(pady=20)

        self.start_button = tk.Button(button_frame, text="Start Server", command=self.start_server)
        self.start_button.grid(row=0, column=1, padx=10)
        
        self.stop_button = tk.Button(button_frame, text="Close", command=self.close_app)
        self.stop_button.grid(row=0, column=2, padx=10)
        
        self.choose_score_button = tk.Button(button_frame, text="Select Score", command=self.choose_score)
        self.choose_score_button.grid(row=0, column=0, padx=10)

        self.status_label = tk.Label(self, text="Server status: Stopped")
        self.status_label.pack(pady=10)
        
    def start_server(self):
        # Check if a score is selected
        if self.selected_score is None:
            tk.messagebox.showwarning("No Selection", "Please select a score first")
            return
        
        score_id, score_title, score_user_id = self.selected_score

        self.run_newmain_script(score_id, score_title, score_user_id)

        self.status_label.config(text=f"Server status: Running with {score_title}")
    
    def run_newmain_script(self, score_id, score_title, score_user_id):
        try:  # Handle subprocess errors
            subprocess.Popen([sys.executable, "./main.py", str(score_id), score_title, str(score_user_id)])
        except Exception as e:
            messagebox.showerror("Execution Error", f"Failed to run the server script: {str(e)}")
        
    def close_app(self):
        self.status_label.config(text="App closing...")
        os.kill(os.getpid(), signal.SIGTERM)

    def choose_score(self):
        score_select_window = ScoreSelectWindow(self, self.scores)
        self.wait_window(score_select_window)

    def run_server(self):
        pass

class ScoreSelectWindow(Toplevel):
    def __init__(self, parent, scores):
        super().__init__(parent)
        self.title("Select a Score")
        self.geometry("250x250")

        self.scores = scores  
        
        self.scores_listbox = Listbox(self, selectmode=SINGLE)
        self.scores_listbox.pack(fill="both", expand=True, padx=10, pady=10)

        for score_id, score_data in scores.items():
            self.scores_listbox.insert(tk.END, score_data['title']) 
        
        select_button = tk.Button(self, text="Select", command=self.select_score)
        select_button.pack(pady=5)

    def select_score(self):
        selected_index = self.scores_listbox.curselection()
        if selected_index:
            selected_score_title = self.scores_listbox.get(selected_index)
            selected_score_id = list(self.scores.keys())[selected_index[0]]
            selected_score_user_id = self.scores[selected_score_id]['user_id']

            self.master.selected_score = (selected_score_id, selected_score_title, selected_score_user_id)
            self.master.status_label.config(text=f"Selected score: {selected_score_title}")
        self.destroy()


login_app = LoginApp()
login_app.mainloop()
