from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Label, Footer, Input
from textual.binding import Binding
from textual import on
from .task_store import load_tasks, save_tasks

class TaskCard(Static):
    can_focus = True

    BINDINGS = [
        Binding("left", "move_left", "Move Left", show=False),
        Binding("h", "move_left", "Move Left", show=False),
        Binding("right", "move_right", "Move Right", show=False),
        Binding("l", "move_right", "Move Right", show=False),
        Binding("d", "delete_task", "Delete Task", show=False),
        Binding("backspace", "delete_task", "Delete Task", show=False),
    ]

    def __init__(self, task_text: str, column: str, **kwargs):
        super().__init__(task_text, **kwargs)
        self.task_text = task_text
        self.column = column

    def action_move_left(self):
        self.screen.move_task(self, -1)

    def action_move_right(self):
        self.screen.move_task(self, 1)
        
    def action_delete_task(self):
        self.screen.delete_task(self)

class KanbanScreen(Screen):
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back to OS"), 
        Binding("a", "add_task", "Add New Task")
    ]

    CSS = """
    KanbanScreen {
        background: #0A0A1A;
        align: center middle;
    }
    
    #kanban_title {
        text-align: center;
        width: 100%;
        padding: 1;
        background: #00FFCC;
        color: #000000;
        text-style: bold;
    }
    
    Vertical {
        width: 1fr;
        border: solid #333333;
        padding: 1;
        margin: 1;
        height: 100%;
    }
    
    .col-header {
        text-align: center;
        text-style: bold;
        padding-bottom: 1;
    }

    TaskCard {
        padding: 1;
        margin-bottom: 1;
        border: solid #555555;
        background: #1A1A2E;
        color: #EEEEEE;
        width: 100%;
    }

    TaskCard:focus {
        background: #FF00FF;
        color: #FFFFFF;
        border: solid #FF00FF;
    }

    #add_task_input {
        dock: bottom;
        display: none;
    }

    #add_task_input.-visible {
        display: block;
    }
    """

    def compose(self):
        yield Label("=== SYSTEM SPRINT BOARD ===", id="kanban_title")
        with Horizontal(id="board_container"):
            with Vertical(id="todo_col"):
                yield Label("TODO", classes="col-header")
            with Vertical(id="doing_col"):
                yield Label("DOING", classes="col-header")
            with Vertical(id="done_col"):
                yield Label("DONE", classes="col-header")
        
        yield Input(placeholder="Type your new task and press Enter...", id="add_task_input")
        yield Footer()
    
    def on_mount(self):
        self.refresh_board()

    def refresh_board(self):
        # Remove old task cards before rebuilding
        for card in self.query(TaskCard):
            card.remove()
            
        tasks = load_tasks()
        for task_text in tasks.get("todo", []):
            self.query_one("#todo_col").mount(TaskCard(task_text, "todo"))
        for task_text in tasks.get("doing", []):
            self.query_one("#doing_col").mount(TaskCard(task_text, "doing"))
        for task_text in tasks.get("done", []):
            self.query_one("#done_col").mount(TaskCard(task_text, "done"))

    def action_add_task(self):
        input_widget = self.query_one("#add_task_input")
        if input_widget.has_class("-visible"):
            input_widget.remove_class("-visible")
        else:
            input_widget.add_class("-visible")
            input_widget.focus()

    @on(Input.Submitted, "#add_task_input")
    def on_new_task(self, event: Input.Submitted):
        task_text = event.value.strip()
        if task_text:
            tasks = load_tasks()
            tasks.setdefault("todo", []).append(task_text)
            save_tasks(tasks)
            self.refresh_board()
        
        event.input.value = ""
        event.input.remove_class("-visible")
        
        # Stop the event from bubbling up to the main OS
        event.stop()
        
        # Give focus to the board
        self.focus()

    def move_task(self, card: TaskCard, direction: int):
        cols = ["todo", "doing", "done"]
        try:
            current_idx = cols.index(card.column)
        except ValueError:
            return
            
        new_idx = current_idx + direction
        if 0 <= new_idx < len(cols):
            new_col = cols[new_idx]
            tasks = load_tasks()
            
            # Remove from current column
            if card.task_text in tasks.get(card.column, []):
                tasks[card.column].remove(card.task_text)
                
            # Append to new column
            tasks.setdefault(new_col, []).append(card.task_text)
            
            save_tasks(tasks)
            self.refresh_board()

    def delete_task(self, card: TaskCard):
        tasks = load_tasks()
        if card.task_text in tasks.get(card.column, []):
            tasks[card.column].remove(card.task_text)
            save_tasks(tasks)
            self.refresh_board()