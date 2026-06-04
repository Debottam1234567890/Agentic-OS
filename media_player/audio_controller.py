import os
import signal
import subprocess
import threading

class AudioController:
    def __init__(self):
        self.process = None
        self.is_paused = False
        self._stop_event = threading.Event()
    
    def play(self, file_path=None):
        if file_path is None:
            file_path = os.path.join(os.path.dirname(__file__), "lofi.mp3")
            
        # Check if already running or paused
        if self.process and self.process.poll() is None:
            if self.is_paused:
                os.kill(self.process.pid, signal.SIGCONT)
                self.is_paused = False
            return
            
        if not os.path.exists(file_path):
            return
            
        self.is_paused = False
        self._stop_event.clear()

        def _loop():
            while not self._stop_event.is_set():
                self.process = subprocess.Popen(["afplay", file_path])
                self.process.wait()
                
        threading.Thread(target=_loop, daemon=True).start()

    def pause(self):
        if self.process and self.process.poll() is None and not self.is_paused:
            os.kill(self.process.pid, signal.SIGSTOP)
            self.is_paused = True

    def stop(self):
        self._stop_event.set()
        if self.process and self.process.poll() is None:
            self.process.terminate()
        self.process = None
        self.is_paused = False