import tkinter as tk
from tkinter import Toplevel, Listbox, SINGLE

class ServerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Server App")
        self.geometry("400x150")  
        
        button_frame = tk.Frame(self)
        button_frame.pack(pady=20)

        self.start_button = tk.Button(button_frame, text="Start Server", command=self.start_server)
        self.start_button.grid(row=0, column=1, padx=10)
        
        self.stop_button = tk.Button(button_frame, text="Stop Server", command=self.stop_server)
        self.stop_button.grid(row=0, column=2, padx=10)
        
        self.choose_score_button = tk.Button(button_frame, text="Select Score", command=self.choose_score)
        self.choose_score_button.grid(row=0, column=0, padx=10)

        self.status_label = tk.Label(self, text="Server status: Stopped")
        self.status_label.pack(pady=10)
        
    def start_server(self):
        self.status_label.config(text="Server status: Running")
        
    def stop_server(self):
        self.status_label.config(text="Server status: Stopped")

    def choose_score(self):
        score_select_window = ScoreSelectWindow(self)
        self.wait_window(score_select_window)  # This makes the new window modal.

    def run_server(self):
        pass

class ScoreSelectWindow(Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Select a Score")
        self.geometry("250x250")
        
        self.scores_listbox = Listbox(self, selectmode=SINGLE)
        self.scores_listbox.pack(fill="both", expand=True, padx=10, pady=10)

        scores = ["KiraKira", "Score 2", "Score 3", "Score 4"]  # Add your scores here
        for score in scores:
            self.scores_listbox.insert(tk.END, score)
        
        select_button = tk.Button(self, text="Select", command=self.select_score)
        select_button.pack(pady=5)

    def select_score(self):
        selected_index = self.scores_listbox.curselection()
        if selected_index:
            selected_score = self.scores_listbox.get(selected_index)
            self.master.status_label.config(text=f"Selected score: {selected_score}")
        self.destroy()

# Run the app
app = ServerApp()
app.mainloop()
