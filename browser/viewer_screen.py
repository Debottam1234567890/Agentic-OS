from textual.screen import Screen
from textual.widgets import Static, Footer
from textual.containers import VerticalScroll
from textual.binding import Binding
from rich.text import Text
class BrowserScreen(Screen):
    BINDINGS = [Binding('escape', 'app.pop_screen', 'Close Browser')]
    def __init__(self, content: str):
        super().__init__()
        try:
            self.rendered = Text.from_markup(content)
        except Exception:
            self.rendered = Text(content)
    def compose(self):
        with VerticalScroll(id='browser_scroll'):
            yield Static(self.rendered, id='browser_content', markup=False)
        yield Footer()
