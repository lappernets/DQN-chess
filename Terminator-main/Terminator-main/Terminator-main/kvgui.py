import os
import subprocess
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle

# Đường dẫn Python trong virtual environment
VENV_PYTHON = r"d:/prjct code/Tink-Her-hack-3.0/venv/Scripts/python.exe"

class CustomButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0.2, 0.6, 0.9, 1)
        self.border = (2, 2, 2, 2)
        self.size_hint_y = None
        self.height = 60
        self.font_size = 18

class ChessAIMenu(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 15
        
        # Logo hoặc banner
        self.logo = Image(
            source='chess_logo.png',  # Thêm logo của bạn
            size_hint=(1, 0.3)
        )
        self.add_widget(self.logo)
        
        # Tiêu đề
        self.title = Label(
            text="Chess AI Training System",
            font_size=28,
            bold=True,
            size_hint_y=None,
            height=50
        )
        self.add_widget(self.title)
        
        # Các nút chức năng
        buttons_data = [
            ("Start New Game", self.start_game, (0.2, 0.7, 0.3, 1)),
            ("Train Model", self.train_model, (0.9, 0.6, 0.1, 1)),
            ("View Training History", self.view_history, (0.2, 0.6, 0.9, 1)),
            ("Settings", self.open_settings, (0.5, 0.5, 0.5, 1)),
            ("Quit", self.quit_app, (0.9, 0.2, 0.2, 1))
        ]
        
        for text, callback, color in buttons_data:
            btn = CustomButton(
                text=text,
                background_color=color
            )
            btn.bind(on_press=callback)
            self.add_widget(btn)

    def start_game(self, instance):
        self.show_loading_popup("Starting Game", "Initializing chess game...")
        try:
            subprocess.run([VENV_PYTHON, "custom_game.py"])
        except Exception as e:
            self.show_error_popup("Error", f"Failed to start game: {str(e)}")

    def train_model(self, instance):
        self.show_loading_popup("Training Model", "Starting training process...")
        try:
            subprocess.run([VENV_PYTHON, "train.py"])
            self.show_success_popup("Training Complete", "Model training finished successfully!")
        except Exception as e:
            self.show_error_popup("Error", f"Training failed: {str(e)}")

    def view_history(self, instance):
        # Implement training history viewer
        self.show_info_popup("Training History", "Feature coming soon!")

    def open_settings(self, instance):
        # Implement settings menu
        self.show_info_popup("Settings", "Settings menu coming soon!")

    def quit_app(self, instance):
        self.show_confirmation_popup(
            "Quit Application",
            "Are you sure you want to quit?",
            App.get_running_app().stop
        )

    def show_loading_popup(self, title, message):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message))
        
        progress = ProgressBar(max=100, value=0)
        content.add_widget(progress)
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.7, 0.3),
            auto_dismiss=False
        )
        
        def update_progress(dt):
            progress.value += 1
            if progress.value >= 100:
                popup.dismiss()
                return False
        
        Clock.schedule_interval(update_progress, 0.03)
        popup.open()

    def show_error_popup(self, title, message):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, color=(1, 0, 0, 1)))
        btn = Button(text="OK", size_hint=(1, 0.3))
        content.add_widget(btn)
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.7, 0.4)
        )
        btn.bind(on_press=popup.dismiss)
        popup.open()

    def show_success_popup(self, title, message):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, color=(0, 1, 0, 1)))
        btn = Button(text="OK", size_hint=(1, 0.3))
        content.add_widget(btn)
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.7, 0.4)
        )
        btn.bind(on_press=popup.dismiss)
        popup.open()

    def show_info_popup(self, title, message):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message))
        btn = Button(text="OK", size_hint=(1, 0.3))
        content.add_widget(btn)
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.7, 0.4)
        )
        btn.bind(on_press=popup.dismiss)
        popup.open()

    def show_confirmation_popup(self, title, message, callback):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message))
        
        buttons = BoxLayout(spacing=10, size_hint_y=0.3)
        btn_yes = Button(text="Yes")
        btn_no = Button(text="No")
        buttons.add_widget(btn_yes)
        buttons.add_widget(btn_no)
        content.add_widget(buttons)
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.7, 0.4)
        )
        
        btn_yes.bind(on_press=lambda x: [callback(), popup.dismiss()])
        btn_no.bind(on_press=popup.dismiss)
        popup.open()

class ChessAIApp(App):
    def build(self):
        # Set window size
        Window.size = (800, 600)
        Window.minimum_width, Window.minimum_height = 600, 400
        
        # Set window background color
        Window.clearcolor = (0.95, 0.95, 0.95, 1)
        
        return ChessAIMenu()

if __name__ == "__main__":
    ChessAIApp().run()