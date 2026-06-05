import shutil
from textual.screen import Screen
from textual.widgets import Static, Footer
from textual import work
from ast_graph.parser import build_adjacency_list
from ast_graph.physics import calculate_layout
from ast_graph.renderer import render_graph

class MapScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Back to OS")]
    
    def compose(self):
        yield Static("Initializing AST Map...", id="map_canvas")
        yield Footer()
        
    def on_mount(self) -> None:
        self.generate_map()
        
    @work(thread=True)
    def generate_map(self):
        def update_msg(msg):
            self.query_one("#map_canvas", Static).update(msg)
            
        self.app.call_from_thread(update_msg, "\n[dim cyan]Parsing AST and calculating physics...[/dim cyan]")
        
        try:
            # 1. Parse AST to get dependencies
            graph = build_adjacency_list(".")
            
            term_width, term_height = shutil.get_terminal_size()
            width = term_width - 2
            height = term_height - 2
            
            # 2. Physics simulation to determine positions
            positions = calculate_layout(graph, width=width, height=height, iterations=100)
            
            # 3. Render to ASCII graph
            ascii_art = render_graph(graph, positions, width=width, height=height)
            
            self.app.call_from_thread(update_msg, ascii_art)
        except Exception as e:
            self.app.call_from_thread(update_msg, f"\n[red]Failed to generate AST graph: {str(e)}[/red]")
