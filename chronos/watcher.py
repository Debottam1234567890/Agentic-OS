import os
import time
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from chronos.snapshot import save_checkpoint
class SandboxChangeHandler(FileSystemEventHandler):
    def __init__(self, debounce_seconds=1.0):
        super().__init__()
        self.last_modified = {}
        self.debounce_seconds = debounce_seconds
    def on_modified(self, event):
        if event.is_directory:
            return
        filepath = event.src_path
        filename = os.path.basename(filepath)
        if filename.startswith('.') or filename.endswith('~') or filename.endswith('.bak') or ('__pycache__' in filepath) or ('.chronos_vault' in filepath):
            return
        current_time = time.time()
        last_time = self.last_modified.get(filepath, 0)
        if current_time - last_time > self.debounce_seconds:
            self.last_modified[filepath] = current_time
            save_checkpoint(filepath)
def start_sandbox_watcher(sandbox_dir: str):
    if not os.path.exists(sandbox_dir):
        os.makedirs(sandbox_dir, exist_ok=True)
    event_handler = SandboxChangeHandler(debounce_seconds=2.0)
    observer = Observer()
    observer.schedule(event_handler, sandbox_dir, recursive=True)
    thread = Thread(target=observer.start, daemon=True)
    thread.start()
    return observer
