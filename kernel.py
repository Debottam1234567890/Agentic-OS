# Imports
import json
import os
from datetime import datetime
import psutil
import pyfiglet
import requests

# Textual Imports
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Header, Footer, Static, Input, ProgressBar, Button
from textual import work, on
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
    #news_panel {
        height: 1fr;
        border-top: solid #00FFCC;
        margin-top: 1;
        padding: 1;
        color: #FFFFFF;
    }
    #focus_panel {
        height: 1fr;
        border-top: solid #FF00FF;
        margin-top: 1;
        padding: 1;
        color: #FF0055;
        text-align: center;
        text-style: bold;
    }
    .hidden { display: none; }
    #quiz_buttons {
        height: auto;
        align: center middle;
        margin-top: 1;
        margin-bottom: 1;
    }
    Button {
        margin: 0 1;
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
                yield Static("Fetching Live News...", id="news_panel")
                yield Static("FOCUS MODE", id="focus_panel", classes="hidden")
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
        self.remaining_focus_secs = 0
        self.focus_timer = None
        self.fetch_news()

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

        if user_input.lower().startswith("focus "):
            parts = user_input.split(" ", 1)
            try:
                minutes = int(parts[1])
                self.start_focus_mode(minutes)
            except ValueError:
                self.last_output += "\n[bold #FF0055]Focus Error: Please enter a valid number. Usage: focus <minutes>[/bold #FF0055]\n"
                self.update_chat_panel()
            return

        elif user_input.lower().startswith("log "):
            journal = user_input[4:].strip()
            self.save_journal_entry(journal)
            return

        elif user_input.lower().startswith("quiz "):
            topic = user_input[5:].strip()
            self.last_output += f"\n[dim cyan]> *Generating a challenging quiz about {topic}...*[/dim cyan]\n"
            self.update_chat_panel()
            self.generate_quiz(topic)
            return

        if user_input:
            self.process_request(user_input)
    
    def save_journal_entry(self, message: str):
        self.last_output += "\n[dim cyan]> *Encrypting and saving to Lightning Journal...*[/dim cyan]\n"
        self.update_chat_panel()
        self.process_journal_async(message)
    
    @work(thread=True)
    def process_journal_async(self, message: str):
        prompt = (
            "Read the following journal entry and output EXACTLY ONE category tag enclosed in brackets. "
            "Choose from: [Academics], [Hardware], [Milestone], [Reflection]. "
            "Output absolutely nothing else."
        )
        try:
            response = client.chat.send(
                model="qwen/qwen3-32b",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": message}
                ],
                stream=False
            )
            tag = response.choices[0].message.content.strip()
            if not tag.startswith("["):
                tag = "[Reflection]"
        except Exception:
            tag = "[Reflection]"
            
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        journal_str = f"* {timestamp} - {tag}: {message}\n"
        
        with open(os.path.join(BASE_DIR, "JOURNAL.md"), "a", encoding="utf-8") as f:
            f.write(journal_str)
            
        safe_tag = tag.replace("[", "\\[")
        success_msg = f"[dim green]> \u2714 Journal entry securely logged under {safe_tag}[/dim green]\n"
        
        def display_success():
            self.last_output += success_msg
            self.update_chat_panel()
            
        self.call_from_thread(display_success)

    def _set_output(self, text):
        self.last_output = text
        self.call_from_thread(self.update_chat_panel)

    def _append_output(self, text):
        self.last_output += text
        self.call_from_thread(self.update_chat_panel)

    @work(thread=True)
    def generate_quiz(self, topic: str):
        prompt = (
            f"Generate a single, difficult multiple-choice question about: {topic}. "
            "You MUST return strict JSON matching this schema exactly:\n"
            '{"question": "...", "options": {"A": "...", "B": "...", "C": "...", "D": "..."}, "correct": "<A, B, C, or D>", "explanation": "..."}\n'
            "CRITICAL: Randomize which letter is the correct answer. Do NOT always make it A.\n"
            "Return ONLY the JSON string. Do not use markdown blocks like ```json."
        )
        try:
            response = client.chat.send(
                model="google/gemini-2.5-pro",
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```json"):
                raw = raw[7:-3].strip()
            elif raw.startswith("```"):
                raw = raw[3:-3].strip()
            data = json.loads(raw)
            
            self.quiz_correct_answer = data["correct"]
            self.quiz_explanation = data["explanation"]
            
            def mount_quiz():
                options_text = (
                    f"[bold]A)[/bold] {data['options']['A']}\n"
                    f"[bold]B)[/bold] {data['options']['B']}\n"
                    f"[bold]C)[/bold] {data['options']['C']}\n"
                    f"[bold]D)[/bold] {data['options']['D']}"
                )
                self.last_output += f"\n[bold #FFFF00]\U0001f9e0 QUIZ TIME[/bold #FFFF00]\n{data['question']}\n\n{options_text}\n"
                self.update_chat_panel()
                
                try:
                    old = self.query_one("#quiz_buttons")
                    old.remove()
                except Exception:
                    pass
                
                container = Horizontal(
                    Button("A", id="quiz_btn_A", name="A", variant="primary"),
                    Button("B", id="quiz_btn_B", name="B", variant="primary"),
                    Button("C", id="quiz_btn_C", name="C", variant="primary"),
                    Button("D", id="quiz_btn_D", name="D", variant="primary"),
                    id="quiz_buttons"
                )
                self.query_one("#chat_scroll").mount(container)
                container.scroll_visible()
            
            self.call_from_thread(mount_quiz)
        except Exception as e:
            def show_err():
                self.last_output += f"\n[bold red]Quiz generation failed: {e}[/bold red]\n"
                self.update_chat_panel()
            self.call_from_thread(show_err)

    @on(Button.Pressed)
    def on_quiz_button_pressed(self, event: Button.Pressed):
        if event.button.id and event.button.id.startswith("quiz_btn_"):
            selected = event.button.name
            
            try:
                container = self.query_one("#quiz_buttons")
                container.remove()
            except Exception:
                pass
            
            if selected == getattr(self, "quiz_correct_answer", ""):
                result_msg = f"\n[bold green]CORRECT![/bold green] You selected {selected}.\n[dim]{self.quiz_explanation}[/dim]\n"
            else:
                result_msg = f"\n[bold red]INCORRECT![/bold red] You selected {selected}. The correct answer was {getattr(self, 'quiz_correct_answer', '')}.\n[dim]{getattr(self, 'quiz_explanation', '')}[/dim]\n"
                
            self.last_output += result_msg
            self.update_chat_panel()

    @work(thread=True)
    def fetch_news(self):
        """Background daemon: geolocates user's country and fetches grouped AI-generated news headlines."""
        country = "Global"
        try:
            geo = requests.get("http://ip-api.com/json/", timeout=5).json()
            country = geo.get("country", "Global")
        except Exception:
            pass

        prompt = (
            f"Generate exactly 9 ultra-short news headlines grouped into 3 sections. "
            f"Use EXACTLY this format, with section labels and bullet points:\n\n"
            f"WORLD NEWS\n"
            f"• <headline 1>\n• <headline 2>\n• <headline 3>\n\n"
            f"LOCAL NEWS ({country})\n"
            f"• <headline 1>\n• <headline 2>\n• <headline 3>\n\n"
            f"SPORTS\n"
            f"• <headline 1>\n• <headline 2>\n• <headline 3>\n\n"
            f"Each headline must be a single sentence, max 12 words. No extra text, commentary, or markdown."
        )
        try:
            response = client.chat.send(
                model="google/gemini-2.5-flash",
                messages=[{"role": "user", "content": prompt}],
                stream=False,
            )
            raw = response.choices[0].message.content.strip()
        except Exception as e:
            raw = f"News unavailable: {e}"

        # Parse and color-code the sections
        lines = raw.splitlines()
        formatted_lines = []
        section_styles = {
            "WORLD": ("[bold #00FFCC]🌍 WORLD NEWS[/bold #00FFCC]", "#AAFFEE"),
            "LOCAL": (f"[bold #FFFF00]📍 LOCAL NEWS — {country}[/bold #FFFF00]", "#FFFF99"),
            "SPORTS": ("[bold #FF6600]🏆 SPORTS[/bold #FF6600]", "#FFB266"),
        }
        current_color = "#FFFFFF"
        for line in lines:
            upper = line.strip().upper()
            if upper.startswith("WORLD"):
                header, current_color = section_styles["WORLD"]
                formatted_lines.append(header)
            elif upper.startswith("LOCAL"):
                header, current_color = section_styles["LOCAL"]
                formatted_lines.append(header)
            elif upper.startswith("SPORTS"):
                header, current_color = section_styles["SPORTS"]
                formatted_lines.append(header)
            elif line.strip().startswith("•"):
                formatted_lines.append(f"[{current_color}]{line.strip()}[/{current_color}]")
            elif line.strip():
                formatted_lines.append(line.strip())

        news_markup = "\n".join(formatted_lines)

        def update_news():
            self.query_one("#news_panel", Static).update(
                f"[bold #00FFCC]📡 Live News Feed[/bold #00FFCC]\n\n{news_markup}"
            )
        self.call_from_thread(update_news)


    def start_focus_mode(self, minutes: int):
        """Activates focus mode: hides the news panel and shows the countdown timer."""
        self.remaining_focus_secs = minutes * 60

        self.query_one("#news_panel", Static).add_class("hidden")
        self.query_one("#focus_panel", Static).remove_class("hidden")

        self.last_output += (
            f"\n[bold #FF00FF]\U0001f3af Focus Mode Activated \u2014 {minutes} min. Distractions suppressed.[/bold #FF00FF]\n"
        )
        self.update_chat_panel()

        if self.focus_timer is not None:
            self.focus_timer.stop()
        self.focus_timer = self.set_interval(1.0, self.tick_focus)

    def tick_focus(self):
        """Called every second to decrement and display the focus countdown."""
        if self.remaining_focus_secs <= 0:
            self.focus_timer.stop()
            self.focus_timer = None
            self.query_one("#focus_panel", Static).add_class("hidden")
            self.query_one("#news_panel", Static).remove_class("hidden")
            self.last_output += "\n[bold #00FF00]\u2705 Focus Session Complete! Welcome back.[/bold #00FF00]\n"
            self.update_chat_panel()
            return

        mins, secs = divmod(self.remaining_focus_secs, 60)
        if self.remaining_focus_secs < 60:
            clock_str = f"[bold #FF0055]\u23f1 {mins:02d}:{secs:02d}[/bold #FF0055]"
        else:
            clock_str = f"[bold #FF00FF]\u23f1 {mins:02d}:{secs:02d}[/bold #FF00FF]"

        self.query_one("#focus_panel", Static).update(
            f"\U0001f3af FOCUS MODE\n\n{clock_str}\n\n[dim]Stay locked in.[/dim]"
        )
        self.remaining_focus_secs -= 1

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