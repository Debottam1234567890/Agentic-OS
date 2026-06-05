import json
import os
DATA_FILE = 'tasks.json'
def load_tasks() -> dict:
    if not os.path.exists(DATA_FILE):
        return {'todo': [], 'doing': [], 'done': []}
    else:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
def save_tasks(tasks: dict) -> None:
    with open(DATA_FILE, 'w') as f:
        json.dump(tasks, f, indent=4)
