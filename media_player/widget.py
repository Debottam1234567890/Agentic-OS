from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static, Button

class LoFiWidget(Static):
    
    def compose(self) -> ComposeResult:
        yield Static("🎧 [bold #FF00FF]Lo-Fi Stream[/bold #FF00FF]", id="lofi_header")
        with Horizontal(id="lofi_controls"):
            yield Button("►", id="lofi_play", variant="success")
            yield Button("⏸", id="lofi_pause", variant="warning")
            yield Button("⏹", id="lofi_stop", variant="error")