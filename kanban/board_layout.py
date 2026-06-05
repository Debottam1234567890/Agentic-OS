from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Label, Footer, Input
from textual.binding import Binding
from textual import on
from .task_store import load_tasks, save_tasks
class TaskCard(Static):
    can_focus = True
    BINDINGS = [Binding('left', 'move_left', 'Move Left', show=False), Binding('h', 'move_left', 'Move Left', show=False), Binding('right', 'move_right', 'Move Right', show=False), Binding('l', 'move_right', 'Move Right', show=False), Binding('d', 'delete_task', 'Delete Task', show=False), Binding('backspace', 'delete_task', 'Delete Task', show=False)]
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
    BINDINGS = [Binding('escape', 'app.pop_screen', 'Back to OS'), Binding('a', 'add_task', 'Add New Task')]
    CSS = '\n    KanbanScreen {\n        background: #0A0A1A;\n        align: center middle;\n    }\n    \n    #kanban_title {\n        text-align: center;\n        width: 100%;\n        padding: 1;\n        background: #00FFCC;\n        color: #000000;\n        text-style: bold;\n    }\n    \n    Vertical {\n        width: 1fr;\n        border: solid #333333;\n        padding: 1;\n        margin: 1;\n        height: 100%;\n    }\n    \n    .col-header {\n        text-align: center;\n        text-style: bold;\n        padding-bottom: 1;\n    }\n\n    TaskCard {\n        padding: 1;\n        margin-bottom: 1;\n        border: solid #555555;\n        background: #1A1A2E;\n        color: #EEEEEE;\n        width: 100%;\n    }\n\n    TaskCard:focus {\n        background: #FF00FF;\n        color: #FFFFFF;\n        border: solid #FF00FF;\n    }\n\n    #add_task_input {\n        dock: bottom;\n        display: none;\n    }\n\n    #add_task_input.-visible {\n        display: block;\n    }\n    '
    def compose(self):
        yield Label('=== SYSTEM SPRINT BOARD ===', id='kanban_title')
        with Horizontal(id='board_container'):
            with Vertical(id='todo_col'):
                yield Label('TODO', classes='col-header')
            with Vertical(id='doing_col'):
                yield Label('DOING', classes='col-header')
            with Vertical(id='done_col'):
                yield Label('DONE', classes='col-header')
        yield Input(placeholder='Type your new task and press Enter...', id='add_task_input')
        yield Footer()
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
        if input_widget.has_class('-visible'):
            input_widget.remove_class('-visible')
        else:
            input_widget.add_class('-visible')
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
        event.input.remove_class('-visible')
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
