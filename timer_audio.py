import pygame
import sys
import os

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
#Fixed by Jasper
class CookingTimer:
    def __init__(self, initial_seconds=1800, alarm_filename="Ping.mp3"):
        self.time_left = initial_seconds
        self.is_running = False
        self.alarm_file = resource_path(alarm_filename)
        
        # Initialize Pygame audio mixer
        pygame.mixer.init()

    def start(self):
        """Starts the timer if time remains."""
        if self.time_left > 0:
            self.is_running = True
            return True
        return False

    def pause(self):
        """Pauses the timer and stops any ringing alarm."""
        self.is_running = False
        self.stop_alarm()

    def extend(self, seconds=60):
        """Adds time to the current countdown."""
        self.time_left += seconds

    def reset(self, seconds):
        """Resets the timer to a new duration and stops the alarm."""
        self.is_running = False
        self.stop_alarm()
        self.time_left = seconds

    def decrement(self):
        """Reduces time by 1 second. Returns True if the timer just hit 0."""
        if self.is_running and self.time_left > 0:
            self.time_left -= 1
            if self.time_left <= 0:
                self.is_running = False
                self.play_alarm()
                return True  # Timer finished
        return False

    def get_time_formatted(self):
        """Returns the remaining time as an MM:SS string."""
        mins, secs = divmod(self.time_left, 60)
        return f"{mins:02d}:{secs:02d}"

    def play_alarm(self):
        """Loads and plays the audio file safely."""
        try:
            # Stop any ongoing playback and rewind mixer
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            
            # Load and play fresh
            pygame.mixer.music.load(self.alarm_file)
            pygame.mixer.music.play() 
        except pygame.error as e:
            print(f"Audio playback error: {e}. Make sure '{self.alarm_file}' exists.")

    def stop_alarm(self):
        """Stops the audio playback and unloads the file."""
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        except pygame.error:
            pass

