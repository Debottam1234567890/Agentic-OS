from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Label, Footer, Input, Button
from textual.binding import Binding
from textual import on
from .task_store import load_tasks, save_tasks

class TaskCard(Vertical):
    can_focus = True
    BINDINGS = [Binding('left', 'move_left', 'Move Left', show=False), Binding('h', 'move_left', 'Move Left', show=False), Binding('right', 'move_right', 'Move Right', show=False), Binding('l', 'move_right', 'Move Right', show=False), Binding('d', 'delete_task', 'Delete Task', show=False), Binding('backspace', 'delete_task', 'Delete Task', show=False)]
    def __init__(self, task_text: str, column: str, **kwargs):
        super().__init__(**kwargs)
        self.task_text = task_text
        self.column = column

    def compose(self):
        yield Label(self.task_text)
        with Horizontal(classes="task-buttons"):
            yield Button("◀", id="btn_left", variant="primary")
            yield Button("✖", id="btn_delete", variant="error")
            yield Button("▶", id="btn_right", variant="primary")

    @on(Button.Pressed, "#btn_left")
    def on_btn_left(self, event):
        event.stop()
        self.action_move_left()

    @on(Button.Pressed, "#btn_right")
    def on_btn_right(self, event):
        event.stop()
        self.action_move_right()

    @on(Button.Pressed, "#btn_delete")
    def on_btn_delete(self, event):
        event.stop()
        self.action_delete_task()

    def action_move_left(self):
        self.screen.move_task(self, -1)
    def action_move_right(self):
        self.screen.move_task(self, 1)
    def action_delete_task(self):
        self.screen.delete_task(self)

class KanbanScreen(Screen):
    BINDINGS = [Binding('escape', 'app.pop_screen', 'Back to OS'), Binding('a', 'add_task', 'Add New Task')]
    CSS = '''
    KanbanScreen {
        background: #0A0A1A;
        align: center middle;
    }
    
    #header_container {
        height: 3;
        align: center middle;
        background: #00FFCC;
        width: 100%;
        margin-bottom: 1;
    }

    #kanban_title {
        color: #000000;
        text-style: bold;
        padding-top: 1;
    }
    
    #btn_add_task {
        margin-left: 4;
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
        height: auto;
    }

    TaskCard:focus {
        background: #3B0764;
        color: #FFFFFF;
        border: solid #FF00FF;
    }

    .task-buttons {
        height: auto;
        align: center middle;
        margin-top: 1;
        border: none;
        padding: 0;
    }
    .task-buttons Button {
        min-width: 5;
        margin: 0 1;
    }

    #add_task_input {
        dock: bottom;
        display: none;
    }
    '''
    def compose(self):
        with Horizontal(id="header_container"):
            yield Label('=== SYSTEM SPRINT BOARD ===', id='kanban_title')
            yield Button("Add Task", id="btn_add_task", variant="success")
        with Horizontal(id='board_container'):
            with Vertical(id='todo_col'):
                yield Label('TODO', classes='col-header')
            with Vertical(id='doing_col'):
                yield Label('DOING', classes='col-header')
            with Vertical(id='done_col'):
                yield Label('DONE', classes='col-header')
        yield Input(placeholder='Type your new task and press Enter...', id='add_task_input')
        yield Footer()

    @on(Button.Pressed, "#btn_add_task")
    def on_add_task_btn(self, event):
        event.stop()
        self.action_add_task()
    def on_mount(self):
        self.refresh_board()
    def refresh_board(self):
        for card in self.query(TaskCard):
            card.remove()
        tasks = load_tasks()
        for task_text in tasks.get('todo', []):
            self.query_one('#todo_col').mount(TaskCard(task_text, 'todo'))
        for task_text in tasks.get('doing', []):
            self.query_one('#doing_col').mount(TaskCard(task_text, 'doing'))
        for task_text in tasks.get('done', []):
            self.query_one('#done_col').mount(TaskCard(task_text, 'done'))
    def action_add_task(self):
        input_widget = self.query_one('#add_task_input')
        input_widget.display = not input_widget.display
        if input_widget.display:
            input_widget.focus()
    @on(Input.Submitted, '#add_task_input')
    def on_new_task(self, event: Input.Submitted):
        task_text = event.value.strip()
        if task_text:
            tasks = load_tasks()
            tasks.setdefault('todo', []).append(task_text)
            save_tasks(tasks)
            self.refresh_board()
        event.input.value = ''
        event.input.display = False
        event.stop()
        self.focus()
    def move_task(self, card: TaskCard, direction: int):
        cols = ['todo', 'doing', 'done']
        try:
            current_idx = cols.index(card.column)
        except ValueError:
            return
        new_idx = current_idx + direction
        if 0 <= new_idx < len(cols):
            new_col = cols[new_idx]
            tasks = load_tasks()
            if card.task_text in tasks.get(card.column, []):
                tasks[card.column].remove(card.task_text)
            tasks.setdefault(new_col, []).append(card.task_text)
            save_tasks(tasks)
            self.refresh_board()
    def delete_task(self, card: TaskCard):
        tasks = load_tasks()
        if card.task_text in tasks.get(card.column, []):
            tasks[card.column].remove(card.task_text)
            save_tasks(tasks)
            self.refresh_board()
