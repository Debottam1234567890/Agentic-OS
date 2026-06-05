import os
import json
from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Static, Header, Footer, Label
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.message import Message

class GalaxyCanvas(Static):
    hovered_file = reactive(None)

    class PointHovered(Message):
        def __init__(self, file_path: str | None) -> None:
            self.file_path = file_path
            super().__init__()

    def __init__(self, coordinates_file, **kwargs):
        super().__init__(**kwargs)
        self.points = []
        if os.path.exists(coordinates_file):
            with open(coordinates_file, "r") as f:
                self.points = json.load(f)

    def render(self) -> str:
        width = self.size.width
        height = self.size.height

        if width <= 0 or height <= 0:
            return ""

        grid = [[" " for _ in range(width)] for _ in range(height)]

        for pt in self.points:
            x = int(pt["x"] * (width - 1))
            y = int(pt["y"] * (height - 1))
            
            x = max(0, min(x, width - 1))
            y = max(0, min(y, height - 1))
            
            if self.hovered_file and self.hovered_file == pt["path"]:
                grid[y][x] = "[bold red]O[/bold red]"
            else:
                if grid[y][x] == " ":
                    grid[y][x] = "[bold cyan]*[/bold cyan]"
                else:
                    grid[y][x] = "[bold yellow]*[/bold yellow]" # Overlapping stars

        lines = ["".join(row) for row in grid]
        return "\n".join(lines)

    def on_mouse_move(self, event) -> None:
        mouse_x = event.x
        mouse_y = event.y

        width = self.size.width
        height = self.size.height

        closest = None
        min_dist = float('inf')

        for pt in self.points:
            pt_x = int(pt["x"] * (width - 1))
            pt_y = int(pt["y"] * (height - 1))

            # Terminal characters are roughly 2x as tall as they are wide, 
            # so we scale y distance for circle-like collision
            dist = (mouse_x - pt_x)**2 + ((mouse_y - pt_y)*2)**2
            if dist < min_dist:
                min_dist = dist
                closest = pt

        if min_dist <= 16 and closest: # threshold
            if self.hovered_file != closest["path"]:
                self.hovered_file = closest["path"]
                self.post_message(self.PointHovered(closest["path"]))
        else:
            if self.hovered_file is not None:
                self.hovered_file = None
                self.post_message(self.PointHovered(None))


class GalaxyScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Back to OS")]
    
    CSS = """
    #galaxy_canvas {
        width: 70%;
        height: 100%;
        border: solid cyan;
    }
    #info_panel {
        width: 30%;
        height: 100%;
        border: solid magenta;
        padding: 1;
    }
    #info_title {
        text-style: bold;
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield GalaxyCanvas(
                os.path.join(os.getcwd(), "data_galaxy", "coordinates.json"), 
                id="galaxy_canvas"
            )
            with Vertical(id="info_panel"):
                yield Label("Hover over a star...", id="info_title")
                yield Static("", id="info_content")
        yield Footer()

    def on_galaxy_canvas_point_hovered(self, message: GalaxyCanvas.PointHovered) -> None:
        title = self.query_one("#info_title", Label)
        content = self.query_one("#info_content", Static)

        if message.file_path:
            title.update(f"🔭 {message.file_path}")
            try:
                full_path = os.path.join(os.getcwd(), message.file_path)
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = []
                    for _ in range(15):
                        try:
                            lines.append(next(f))
                        except StopIteration:
                            break
                code_snippet = "".join(lines)
                content.update(f"```python\n{code_snippet}\n```")
            except Exception as e:
                content.update(f"[red]Could not read file: {e}[/red]")
        else:
            title.update("Hover over a star...")
            content.update("")
