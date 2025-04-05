import os
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.font import Font
import json
from datetime import datetime

class ChessAIMenu:
    def __init__(self):
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.VENV_PYTHON = os.path.expanduser(r"~\venv\Scripts\python.exe")
        self.CUSTOM_GAME_SCRIPT = os.path.join(self.BASE_DIR, "custom_game.py")
        self.TRAIN_SCRIPT = os.path.join(self.BASE_DIR, "train.py")
        self.HISTORY_FILE = os.path.join(self.BASE_DIR, "training_history.json")
        
        self.setup_main_window()
        self.create_widgets()
        self.load_history()

    def setup_main_window(self):
        self.root = tk.Tk()
        self.root.title("Chess AI Training System")
        self.root.geometry("600x500")
        self.root.configure(bg="#2C3E50")
        
        # Custom styles
        self.style = ttk.Style()
        self.style.configure("Custom.TButton",
                           padding=10,
                           font=("Arial", 12))
        
        # Custom fonts
        self.header_font = Font(family="Arial", size=24, weight="bold")
        self.button_font = Font(family="Arial", size=12)
        self.status_font = Font(family="Arial", size=10, slant="italic")

    def create_widgets(self):
        # Main container
        self.main_frame = tk.Frame(self.root, bg="#2C3E50")
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # Header
        header = tk.Label(self.main_frame,
                         text="Chess AI Training System",
                         font=self.header_font,
                         fg="white",
                         bg="#2C3E50")
        header.pack(pady=20)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = tk.Label(self.main_frame,
                                  textvariable=self.status_var,
                                  font=self.status_font,
                                  fg="#BDC3C7",
                                  bg="#2C3E50")
        self.status_bar.pack(pady=(0, 20))

        # Buttons frame
        buttons_frame = tk.Frame(self.main_frame, bg="#2C3E50")
        buttons_frame.pack(fill="x", padx=50)

        # Buttons
        buttons = [
            ("Start New Game", self.run_custom_game, "#3498DB"),
            ("Train Model", self.run_training, "#27AE60"),
            ("View History", self.show_history, "#9B59B6"),
            ("Settings", self.show_settings, "#F39C12"),
            ("Quit", self.quit_app, "#E74C3C")
        ]

        for text, command, color in buttons:
            btn = tk.Button(buttons_frame,
                          text=text,
                          command=command,
                          font=self.button_font,
                          bg=color,
                          fg="white",
                          relief="flat",
                          width=20)
            btn.pack(pady=10)
            
            # Hover effects
            btn.bind("<Enter>", lambda e, b=btn: self.on_hover(e, b))
            btn.bind("<Leave>", lambda e, b=btn: self.on_leave(e, b))

        # Progress bar
        self.progress = ttk.Progressbar(self.main_frame,
                                      orient="horizontal",
                                      length=400,
                                      mode="determinate")
        self.progress.pack(pady=20)

    def on_hover(self, event, button):
        """Button hover effect"""
        button.configure(relief="raised")

    def on_leave(self, event, button):
        """Button leave effect"""
        button.configure(relief="flat")

    def update_status(self, message):
        """Update status bar message"""
        self.status_var.set(message)
        self.root.update()

    def show_progress(self, value):
        """Update progress bar"""
        self.progress["value"] = value
        self.root.update()

    def load_history(self):
        """Load training history from file"""
        try:
            if os.path.exists(self.HISTORY_FILE):
                with open(self.HISTORY_FILE, 'r') as f:
                    self.history = json.load(f)
            else:
                self.history = []
        except:
            self.history = []

    def save_history(self, session_info):
        """Save training session to history"""
        self.history.append(session_info)
        with open(self.HISTORY_FILE, 'w') as f:
            json.dump(self.history, f)

    def run_script(self, script_path, description):
        """Run Python script with error handling"""
        if not os.path.exists(script_path):
            messagebox.showerror("Error", f"{description} script not found:\n{script_path}")
            return False
        
        try:
            self.update_status(f"Running {description}...")
            self.show_progress(50)
            subprocess.run([self.VENV_PYTHON, script_path], check=True)
            self.show_progress(100)
            return True
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Error running {description}:\n{str(e)}")
            return False
        finally:
            self.show_progress(0)
            self.update_status("Ready")

    def run_custom_game(self):
        """Run chess game and training sequence"""
        if messagebox.askyesno("Start Game", "Would you like to start a new game?"):
            if self.run_script(self.CUSTOM_GAME_SCRIPT, "Chess game"):
                self.save_history({
                    "type": "game",
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "completed"
                })
                if messagebox.askyesno("Training", "Would you like to train the model with the new game data?"):
                    self.run_training()

    def run_training(self):
        """Run model training"""
        self.update_status("Training model...")
        if self.run_script(self.TRAIN_SCRIPT, "Training"):
            self.save_history({
                "type": "training",
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "completed"
            })
            messagebox.showinfo("Success", "Training completed successfully!")

    def show_history(self):
        """Show training history window"""
        history_window = tk.Toplevel(self.root)
        history_window.title("Training History")
        history_window.geometry("400x300")
        history_window.configure(bg="#2C3E50")

        # History list
        history_frame = tk.Frame(history_window, bg="#2C3E50")
        history_frame.pack(fill="both", expand=True, padx=20, pady=20)

        if not self.history:
            tk.Label(history_frame,
                    text="No history available",
                    fg="white",
                    bg="#2C3E50").pack()
        else:
            for session in reversed(self.history):
                session_frame = tk.Frame(history_frame, bg="#34495E", relief="raised", bd=1)
                session_frame.pack(fill="x", pady=5)
                
                tk.Label(session_frame,
                        text=f"{session['type'].title()} - {session['date']}",
                        fg="white",
                        bg="#34495E").pack(pady=5)

    def show_settings(self):
        """Show settings window"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x300")
        settings_window.configure(bg="#2C3E50")

        # Add settings options here
        tk.Label(settings_window,
                text="Settings coming soon!",
                fg="white",
                bg="#2C3E50").pack(pady=20)

    def quit_app(self):
        """Quit application"""
        if messagebox.askyesno("Quit", "Are you sure you want to quit?"):
            self.root.quit()

    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = ChessAIMenu()
    app.run()