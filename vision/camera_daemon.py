import subprocess
import os
import time
def capture_screen(delay: int=0, out_file='vision_scratch.png') -> str:
    full_path = os.path.join(os.getcwd(), out_file)
    if delay > 0:
        time.sleep(delay)
    subprocess.run(['screencapture', '-x', '-m', full_path], check=True)
    return full_path
