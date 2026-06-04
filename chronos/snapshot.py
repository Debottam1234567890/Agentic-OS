import os
import shutil
import datetime

VAULT_DIR = os.path.join(os.getcwd(), ".chronos_vault")


def init_vault():
    os.makedirs(VAULT_DIR, exist_ok=True)


def save_checkpoint(filepath: str) -> str:
    """Silently snapshot a file into the Chronos vault."""
    if not os.path.exists(filepath):
        return f"[red]File not found: {filepath}[/red]"
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.basename(filepath)
    backup_path = os.path.join(VAULT_DIR, f"{filename}.{timestamp}.bak")
    shutil.copy2(filepath, backup_path)
    return backup_path


def auto_checkpoint_dir(directory: str) -> int:
    """Checkpoint every file in a directory. Returns number of files saved."""
    if not os.path.isdir(directory):
        return 0
    count = 0
    for f in os.listdir(directory):
        full = os.path.join(directory, f)
        if os.path.isfile(full) and not f.startswith("."):
            save_checkpoint(full)
            count += 1
    return count