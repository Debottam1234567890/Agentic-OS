# Imports
import json
import os
from datetime import datetime
import psutil
import pyfiglet

# Textual Imports
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Header, Footer, Static, Input, ProgressBar
from textual import work
from rich.console import Group
from rich.markdown import Markdown as RichMarkdown
from rich.markup import escape

# pyrefly: ignore [missing-import]
from openrouter import OpenRouter

from logic_router import route_intent
from agents.terminal_agent import execute_terminal_agent
from agents.conversational_agent import stream_conversational_agent
from agents.web_agent import stream_web_agent

client = OpenRouter(
    api_key=os.environ.get("OPENROUTER_API_KEY", ""),
    server_url="https://ai.hackclub.com/proxy/v1"
)

BASE_DIR = os.getcwd()
MEMORY_FILE = os.path.join(BASE_DIR, ".os_memory.json")

class KernelOS(App):
    CSS = """
    Screen {
        layout: vertical;
        background: #0A0A1A;
    }
    Header {
        dock: top;
        height: 3;
        background: #000000;
        color: #00FFCC;
        border-bottom: heavy #FF00FF;
    }
    #cpu_alert {
        background: #FF0055;
        color: #FFFFFF;
        text-align: center;
        text-style: bold italic;
        height: 3;
        display: none;
        border-bottom: solid #FFFFFF;
    }
    #cpu_alert.visible {
        display: block;
    }
    #body {
        layout: horizontal;
        height: 1fr;
    }
    #chat_scroll {
        width: 3fr;
        height: 1fr;
        border: double #00FFCC;
        background: #0A0A1A;
    }
    #main_chat {
        height: auto;
        padding: 1;
        background: #0A0A1A;
    }
    #sidebar {
        width: 1fr;
        height: 1fr;
        border: heavy #FF00FF;
        padding: 1 2;
        background: #110011;
    }
    #sidebar Static {
        margin-top: 1;
        text-style: bold;
        color: #FFFF00;
    }
    #sidebar ProgressBar {
        margin-bottom: 2;
    }
    #sidebar ProgressBar > .bar--bar {
        color: #00FF00;
    }
    Input {
        dock: bottom;
        border-top: double #00FFCC;
        background: #000000;
        color: #FF00FF;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("Warning! Your CPU is over 85%!", id="cpu_alert")
        with Horizontal(id="body"):
            with VerticalScroll(id="chat_scroll"):
                yield Static(id="main_chat")
            with Vertical(id="sidebar"):
                yield Static("CPU Usage", id="cpu_usage")
                yield ProgressBar(total=100, show_eta=False, id="cpu_bar")
                yield Static("RAM Usage", id="ram_usage")
                yield ProgressBar(total=100, show_eta=False, id="ram_bar")
                yield Static("Disk Usage", id="disk_usage")
                yield ProgressBar(total=100, show_eta=False, id="disk_bar")
        yield Input(placeholder=">>> ", id="user_input")
        yield Footer()

    def on_mount(self):
        os.makedirs("sandbox", exist_ok=True)
        self.title = os.getcwd()
        self.system_status = {"cpu_alert": False, "last_recorded_cpu": 0, "last_recorded_ram": 0}
        
        self.agent_title = "System Boot"
        self.agent_color = "#00FFCC"
        self.last_command = "System Initialization."
        
        ascii_banner = pyfiglet.figlet_format("AGENTIC OS", font="slant")
        escaped_banner = escape(ascii_banner)
        self.last_output = f"[bold #00FFCC]{escaped_banner}[/bold #00FFCC]\n"
        
        self.update_telemetry()
        self.set_interval(2.0, self.update_telemetry)
        self.update_chat_panel()
        
        self.run_boot_sequence()

    @work
    async def run_boot_sequence(self):
        import asyncio
        system_check_strs = ["Loading kernel", "Loading AI engine", "Loading memory logs", "Checking CPU registers", "Initializing cognitive arrays"]
        
        for phase in system_check_strs:
            self.last_output += f"[{'#00FF00'}]✔[/{'#00FF00'}] {phase}\n"
            self.update_chat_panel()
            await asyncio.sleep(1)
            
        self.system_memory = []
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r") as file:
                self.system_memory = json.load(file)
            init_msg = f"[dim #00FFCC]Memory Module: Loaded {len(self.system_memory)} previous logs.[/dim #00FFCC]"
        else:
            init_msg = f"[dim #FFFF00]Memory Module: No previous memory found. Starting fresh.[/dim #FFFF00]"
            
        self.last_output += init_msg + f"\n\n[bold {'#00FF00'}] ✔ SYSTEM READY ✔ [/bold {'#00FF00'}]"
        self.update_chat_panel()
        self.query_one(Input).focus()

    def update_telemetry(self):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        self.system_status["last_recorded_cpu"] = cpu
        self.system_status["last_recorded_ram"] = ram
        
        self.query_one("#cpu_usage", Static).update(f"CPU Usage: {cpu}%")
        self.query_one("#cpu_bar", ProgressBar).progress = cpu
        
        self.query_one("#ram_usage", Static).update(f"RAM Usage: {ram}%")
        self.query_one("#ram_bar", ProgressBar).progress = ram
        
        self.query_one("#disk_usage", Static).update(f"Disk Usage: {disk}%")
        self.query_one("#disk_bar", ProgressBar).progress = disk
        
        alert = self.query_one("#cpu_alert", Static)
        if cpu > 85:
            alert.add_class("visible")
        else:
            alert.remove_class("visible")

    def update_chat_panel(self):
        chat_scroll = self.query_one("#chat_scroll", VerticalScroll)
        main_chat = self.query_one("#main_chat", Static)
        
        chat_scroll.border_title = f"[{self.agent_color}]{self.agent_title}[/{self.agent_color}]"
        chat_scroll.styles.border = ("double", self.agent_color)
        
        if self.agent_title in ["Conversational Agent", "Web Agent"]:
            chat_content = Group(f"[{self.agent_color}]{self.last_command}[/{self.agent_color}]", RichMarkdown(self.last_output))
            main_chat.update(chat_content)
        else:
            chat_content = f"[{self.agent_color}]{self.last_command}[/{self.agent_color}]\n{self.last_output}"
            main_chat.update(chat_content)
        
        self.title = os.getcwd()
        self.call_after_refresh(chat_scroll.scroll_end, animate=False)

    async def on_input_submitted(self, event: Input.Submitted):
        user_input = event.value.strip()
        event.input.value = ""
        
        termination_keywords = ["exit", "quit", "bye", "terminate", "shutdown"]
        if user_input.lower() in termination_keywords:
            self.exit()
            return
            
        if user_input:
            self.process_request(user_input)

    def _set_output(self, text):
        self.last_output = text
        self.call_from_thread(self.update_chat_panel)

    def _append_output(self, text):
        self.last_output += text
        self.call_from_thread(self.update_chat_panel)

    @work(thread=True)
    def process_request(self, user_input: str):
        current_dir = os.getcwd()
        visible_files = ", ".join(os.listdir(current_dir)[:20])
        recent_history = json.dumps(self.system_memory[-5:], indent=2)
        
        intent_category = route_intent(user_input, client)
        
        command_run = ""
        stdout_val = ""
        stderr_val = ""
        returncode = 0

        if "TERMINAL" in intent_category:
            res = execute_terminal_agent(user_input, current_dir, visible_files, recent_history, client, self._append_output)
            self.agent_title = res["agent_title"]
            self.agent_color = res["agent_color"]
            self.last_command = res["command"]
            self.last_output = res["output"]
            
            if res["new_dir"] and os.path.isdir(res["new_dir"]) and os.getcwd() != res["new_dir"]:
                os.chdir(res["new_dir"])
                
            command_run = res["command"]
            stdout_val = res["stdout"]
            stderr_val = res["stderr"]
            returncode = res["returncode"]
            
        elif "CONVERSATIONAL" in intent_category:
            self.agent_title = "Conversational Agent"
            self.agent_color = "#FF00FF"
            self.last_command = user_input
            self.last_output = ""
            self.call_from_thread(self.update_chat_panel)
            
            res = stream_conversational_agent(user_input, client, self._append_output, self.system_memory)
            command_run = res["command"]
            stdout_val = res["output"]
            
        elif "WEB" in intent_category:
            self.agent_title = "Web Agent"
            self.agent_color = "#FFFF00"
            self.last_command = f"Web Search: Initiated..."
            
            res = stream_web_agent(user_input, client, self._set_output, self._append_output)
            self.last_command = res["command"]
            
            command_run = res["command"]
            stdout_val = res["output"]
            
        else:
            self.agent_title = "System Error"
            self.agent_color = "#FF0055"
            self.last_command = "Routing Error"
            self.last_output = "The Cognitive Router returned an invalid category."
            
            command_run = "Routing Error"
            stdout_val = self.last_output
            
        session_log = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_intent": user_input,
            "generated_command": command_run,
            "stdout": stdout_val if returncode == 0 else "",
            "stderr": stderr_val if returncode != 0 else "",
        }
        self.system_memory.append(session_log)
        with open(MEMORY_FILE, "w") as file:
            json.dump(self.system_memory, file, indent=4)
            
        self.call_from_thread(self.update_chat_panel)

if __name__ == "__main__":
    from rich.console import Console
    console = Console()

    # Pre-boot: Force ChromaDB's ONNX model download in the main thread.
    # This MUST happen before app.run() to avoid the macOS fds_to_keep crash.
    print("Booting Knowledge Vault...")
    # pyrefly: ignore [missing-import]
    import chromadb
    _client = chromadb.PersistentClient(path="./physics_db")
    _collection = _client.get_or_create_collection(name="physics_vault")
    _collection.upsert(documents=["warmup"], ids=["__warmup__"])
    print("Knowledge Vault online.")

    app = KernelOS()
    app.run()
    console.print("\n[dim yellow]Shutting down the system! Goodbye![/dim yellow]")