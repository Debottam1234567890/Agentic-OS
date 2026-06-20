from browser.engine import fetch_and_clean_html
import json
import os
from datetime import datetime
import psutil
import pyfiglet
import requests
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Header, Footer, Static, Input, ProgressBar, Button
from textual import work, on
from rich.console import Group
from rich.markdown import Markdown as RichMarkdown
from rich.markup import escape
from openrouter import OpenRouter
from logic_router import route_intent
from agents.terminal_agent import execute_terminal_agent
from agents.conversational_agent import stream_conversational_agent
from agents.web_agent import stream_web_agent
from browser.viewer_screen import BrowserScreen
from media_player.audio_controller import AudioController
from media_player.widget import LoFiWidget
from voice.microphone_daemon import record_scratch_audio
from voice.transcriber import transcribe_wav
from kanban.board_layout import KanbanScreen
from neural_find.searcher import semantic_search
from vision.camera_daemon import capture_screen
from vision.analyzer import analyze_image
from headless.automation_agent import execute_web_automation
from chronos.snapshot import save_checkpoint, init_vault, auto_checkpoint_dir
from chronos.rewind import rollback_file
from data_galaxy.pipeline import build_galaxy
from data_galaxy.galaxy_screen import GalaxyScreen
from chronos.watcher import start_sandbox_watcher
from stock_market.ui import StockScreen
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)
def get_api_key():
    key = os.environ.get('OPENROUTER_API_KEY', '').strip()
    if not key:
        api_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'api.txt')
        if os.path.exists(api_path):
            with open(api_path, 'r') as f:
                key = f.readline().strip()
    return key
client = OpenRouter(api_key=get_api_key(), server_url='https://ai.hackclub.com/proxy/v1')
original_send = client.chat.send
def _fallback_send(*args, **kwargs):
    fallback = 'openrouter:free'
    is_stream = kwargs.get('stream', False)
    if is_stream:
        def _gen():
            try:
                for chunk in original_send(*args, **kwargs):
                    yield chunk
            except Exception:
                kwargs['model'] = fallback
                for chunk in original_send(*args, **kwargs):
                    yield chunk
        return _gen()
    else:
        try:
            return original_send(*args, **kwargs)
        except Exception:
            kwargs['model'] = fallback
            return original_send(*args, **kwargs)
client.chat.send = _fallback_send
BASE_DIR = os.getcwd()
MEMORY_FILE = os.path.join(BASE_DIR, '.os_memory.json')
def get_recent_code_context(base_dir='.') -> str:
    recent_file = None
    recent_time = 0
    for root, dirs, files in os.walk(base_dir):
        if '.git' in root or 'venv' in root or '__pycache__' in root:
            continue
        for f in files:
            if f.endswith(('.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css')):
                full_path = os.path.join(root, f)
                mtime = os.path.getmtime(full_path)
                if mtime > recent_time:
                    recent_time = mtime
                    recent_file = full_path
    if recent_file:
        try:
            with open(recent_file, 'r') as f:
                content = f.read()
            return f'--- {os.path.basename(recent_file)} ---\n{content}'
        except Exception:
            pass
    return ''
class KernelOS(App):
    SCREENS = {'kanban': KanbanScreen, 'browser': BrowserScreen}
    CSS = '\n    Screen {\n        layout: vertical;\n        background: #0F172A; /* Slate 900 */\n    }\n    Header {\n        dock: top;\n        height: 3;\n        background: #020617;\n        color: #38BDF8; /* Sky 400 */\n        border-bottom: round #1E293B;\n    }\n    #cpu_alert {\n        background: #EF4444; /* Red 500 */\n        color: #FFFFFF;\n        text-align: center;\n        text-style: bold italic;\n        height: 3;\n        display: none;\n        border-bottom: solid #FFFFFF;\n    }\n    #cpu_alert.visible {\n        display: block;\n    }\n    #body {\n        layout: horizontal;\n        height: 1fr;\n    }\n    #chat_scroll {\n        width: 3fr;\n        height: 1fr;\n        border: round #38BDF8;\n        background: #0F172A;\n        padding: 0 1;\n        transition: border 0.5s;\n    }\n    #chat_scroll.system-ready {\n        border: round #10B981; /* Emerald 500 */\n    }\n    #main_chat {\n        height: auto;\n        padding: 1;\n        background: #0F172A;\n    }\n    #sidebar {\n        width: 1fr;\n        height: 1fr;\n        border: round #818CF8; /* Indigo 400 */\n        padding: 1 2;\n        background: #1E293B; /* Slate 800 */\n        transition: border 0.5s, background 0.5s;\n    }\n    #sidebar.warning-mode {\n        border: round #EF4444;\n        background: #450A0A;\n    }\n    #sidebar.warning-mode Static {\n        color: #FCA5A5;\n        transition: color 0.5s;\n    }\n    #sidebar.warning-mode ProgressBar > .bar--bar {\n        color: #EF4444;\n    }\n    #sidebar Static {\n        margin-top: 1;\n        text-style: bold;\n        color: #E2E8F0; /* Slate 200 */\n    }\n    #sidebar ProgressBar {\n        margin-bottom: 2;\n    }\n    #sidebar ProgressBar > .bar--bar {\n        color: #10B981; /* Emerald 500 */\n    }\n    #sidebar ProgressBar > .bar--background {\n        background: #334155; /* Slate 700 */\n    }\n    Input {\n        dock: bottom;\n        border-top: round #38BDF8;\n        background: #020617;\n        color: #D946EF;\n    }\n    #news_panel {\n        height: 1fr;\n        border-top: dashed #475569;\n        margin-top: 1;\n        padding: 1 0;\n        color: #F8FAFC;\n        overflow-y: auto;\n    }\n    #focus_panel {\n        height: 1fr;\n        border-top: solid #F472B6;\n        margin-top: 1;\n        padding: 1;\n        color: #F472B6;\n        text-align: center;\n        text-style: bold;\n    }\n    .hidden { display: none; }\n    #quiz_buttons {\n        height: auto;\n        align: center middle;\n        margin-top: 1;\n        margin-bottom: 1;\n    }\n    Button {\n        margin: 0 1;\n    }\n    LoFiWidget { border-top: dashed #475569; margin-top: 1; padding: 1; height: auto; }\n    #lofi_controls { height: auto; align: center middle; margin-top: 1; }\n    #lofi_header { text-align: center; }\n    '
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static('Warning! Your CPU is over 85%!', id='cpu_alert')
        with Horizontal(id='body'):
            with VerticalScroll(id='chat_scroll'):
                yield Static(id='main_chat')
            with Vertical(id='sidebar'):
                yield Static('CPU:', id='cpu_usage')
                yield ProgressBar(total=100, show_eta=False, id='cpu_bar')
                yield Static('RAM:', id='ram_usage')
                yield ProgressBar(total=100, show_eta=False, id='ram_bar')
                yield Static('Disk:', id='disk_usage')
                yield ProgressBar(total=100, show_eta=False, id='disk_bar')
                yield Static('Fetching Live News...', id='news_panel')
                yield Static('FOCUS MODE', id='focus_panel', classes='hidden')
        yield Input(placeholder='>>> ', id='user_input')
        yield Footer()
    def on_mount(self):
        init_vault()
        start_sandbox_watcher(os.getcwd())
        self.title = os.getcwd()
        self.system_status = {'cpu_alert': False, 'last_recorded_cpu': 0, 'last_recorded_ram': 0}
        self.agent_title = 'System Boot'
        self.agent_color = '#00FFCC'
        self.last_command = 'System Initialization.'
        self.audio_system = AudioController()
        chat_scroll = self.query_one('#chat_scroll')
        chat_scroll.styles.opacity = 0.0
        chat_scroll.styles.animate('opacity', value=1.0, duration=2.0)
        self.last_output = ''
        self.update_telemetry()
        self.set_interval(0.5, self.update_telemetry)
        self.run_boot_sequence()
        self.remaining_focus_secs = 0
        self.focus_timer = None
        self.fetch_news()
    @work(thread=True)
    async def run_boot_sequence(self):
        import asyncio
        import pyfiglet
        from rich.markup import escape
        ascii_banner = pyfiglet.figlet_format('AGENTIC OS', font='slant')
        escaped_banner = escape(ascii_banner)
        self.last_output = f'[bold #00FFCC]{escaped_banner}[/bold #00FFCC]\n'
        self.app.call_from_thread(self.update_chat_panel)
        system_check_strs = ['Loading kernel', 'Loading AI engine', 'Loading memory logs', 'Checking CPU registers', 'Initializing cognitive arrays']
        spinners = ['/', '-', '\\', '|']
        for phase in system_check_strs:
            for i in range(4):
                spinner = spinners[i % len(spinners)]
                temp_output = self.last_output + f"[{'#FFFF00'}]{spinner}[/{'#FFFF00'}] {phase}\n"
                def update_spin(t=temp_output):
                    self.query_one('#main_chat', Static).update(f'[{self.agent_color}]{self.last_command}[/{self.agent_color}]\n{t}')
                self.app.call_from_thread(update_spin)
                await asyncio.sleep(0.1)
            self.last_output += f"[{'#00FF00'}]✔[/{'#00FF00'}] {phase}\n"
            self.app.call_from_thread(self.update_chat_panel)
            await asyncio.sleep(0.2)
        self.system_memory = []
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r') as file:
                self.system_memory = json.load(file)
            init_msg = f'[dim #00FFCC]Memory Module: Loaded {len(self.system_memory)} previous logs.[/dim #00FFCC]'
        else:
            init_msg = f'[dim #FFFF00]Memory Module: No previous memory found. Starting fresh.[/dim #FFFF00]'
        self.last_output += init_msg + f'\n\n[bold #00FF00] ✔ SYSTEM READY ✔ [/bold #00FF00]'
        self.app.call_from_thread(self.update_chat_panel)
        def finalize_boot():
            chat = self.query_one('#chat_scroll')
            chat.add_class('system-ready')
            self.set_timer(1.0, lambda: chat.remove_class('system-ready'))
            try:
                self.query_one(Input).focus()
            except Exception:
                pass
            
            onboarding_msg = (
                "\n\n[bold #38BDF8]Welcome to Agentic OS. Here is your quickstart guide:[/bold #38BDF8]\n\n"
                "• [bold]Natural Language[/bold]: Just type what you want to do (e.g. 'Write a python script that...')\n"
                "• [bold]browse <url>[/bold]: Autonomously load and read a webpage.\n"
                "• [bold]stock <ticker>[/bold]: Launch native charts for a stock (e.g., 'stock AAPL').\n"
                "• [bold]look[/bold]: Use the camera to see what's on your screen and debug errors.\n"
                "• [bold]listen[/bold]: Start the microphone to give voice commands.\n"
                "• [bold]headless <task>[/bold]: Spin up an invisible browser to interact with a site.\n"
                "• [bold]rewind <file>[/bold]: Rollback a file to its previous state.\n"
                "• [bold]map core[/bold]: Visualize the Python codebase syntax tree.\n"
                "• [bold]galaxy[/bold]: Build a 3D semantic data galaxy.\n"
                "• [bold]focus <minutes>[/bold]: Enter distraction-free mode.\n"
                "• [bold]lofi start[/bold]: Play ambient background music.\n"
                "• [bold]tasks[/bold]: Open the Kanban board.\n"
            )
            self.last_output += onboarding_msg
            self.update_chat_panel()

        self.app.call_from_thread(finalize_boot)
    def update_telemetry(self):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        self.system_status['last_recorded_cpu'] = cpu
        self.system_status['last_recorded_ram'] = ram
        self.query_one('#cpu_usage', Static).update(f'CPU: {cpu}%')
        self.query_one('#cpu_bar', ProgressBar).progress = cpu
        self.query_one('#ram_usage', Static).update(f'RAM: {ram}%')
        self.query_one('#ram_bar', ProgressBar).progress = ram
        self.query_one('#disk_usage', Static).update(f'Disk: {disk}%')
        self.query_one('#disk_bar', ProgressBar).progress = disk
        alert = self.query_one('#cpu_alert', Static)
        sidebar = self.query_one('#sidebar')
        if cpu > 85:
            alert.add_class('visible')
            sidebar.add_class('warning-mode')
        else:
            alert.remove_class('visible')
            sidebar.remove_class('warning-mode')
    def update_chat_panel(self):
        chat_scroll = self.query_one('#chat_scroll', VerticalScroll)
        main_chat = self.query_one('#main_chat', Static)
        chat_scroll.border_title = f'[{self.agent_color}]{self.agent_title}[/{self.agent_color}]'
        chat_scroll.styles.border = ('double', self.agent_color)
        if self.agent_title in ['Conversational Agent', 'Web Agent', 'Omni-Sight']:
            chat_content = Group(f'[{self.agent_color}]{self.last_command}[/{self.agent_color}]', RichMarkdown(self.last_output))
            main_chat.update(chat_content)
        else:
            chat_content = f'[{self.agent_color}]{self.last_command}[/{self.agent_color}]\n{self.last_output}'
            main_chat.update(chat_content)
        self.title = os.getcwd()
        self.call_after_refresh(chat_scroll.scroll_end, animate=False)
    async def on_input_submitted(self, event: Input.Submitted):
        user_input = event.value.strip()
        event.input.value = ''
        termination_keywords = ['exit', 'quit', 'bye', 'terminate', 'shutdown']
        if user_input.lower() in termination_keywords:
            try:
                for static in self.query('Static'):
                    static.update('')
            except Exception:
                pass
            self.exit()
            return
        if user_input.lower().startswith('focus '):
            parts = user_input.split(' ', 1)
            try:
                minutes = int(parts[1])
                self.start_focus_mode(minutes)
            except ValueError:
                self.last_output += '\n[bold #FF0055]Focus Error: Please enter a valid number. Usage: focus <minutes>[/bold #FF0055]\n'
                self.update_chat_panel()
            return
        elif user_input.lower().startswith('log '):
            journal = user_input[4:].strip()
            self.save_journal_entry(journal)
            return
        elif user_input.lower().startswith('quiz '):
            topic = user_input[5:].strip()
            self.last_output += f'\n[dim cyan]> *Generating a challenging quiz about {topic}...*[/dim cyan]\n'
            self.update_chat_panel()
            self.generate_quiz(topic)
            return
        elif user_input.startswith('browse '):
            url = user_input[7:].strip()
            self.agent_title = 'Web Navigator'
            self.agent_color = '#00FFCC'
            self.last_command = user_input
            self.last_output = f'[dim cyan]> *Fetching and stripping {url}...*[/dim cyan]\n'
            self.update_chat_panel()
            self.launch_browser(url)
            return
        elif user_input.lower() == 'lofi start':
            if not self.query('LoFiWidget'):
                self.query_one('#sidebar').mount(LoFiWidget())
            self.agent_title = 'Media Controller'
            self.agent_color = '#00FFCC'
            self.last_command = user_input
            self.last_output = '[dim cyan]> *Mounting Lo-Fi subsystem...*[/dim cyan]\n'
            self.update_chat_panel()
            self.audio_system.play()
            return
        elif user_input.lower() == 'tasks':
            self.push_screen(KanbanScreen())
            return
        elif user_input.lower() == 'listen':
            self.agent_title = 'Voice Agent'
            self.agent_color = '#FF0055'
            self.last_command = 'Voice Input Mode'
            self.last_output = '\n[bold red]🎤 Listening for 5 seconds...[/bold red]\n'
            self.update_chat_panel()
            self.run_voice_pipeline()
            return
        elif user_input.lower().startswith('search '):
            query = user_input[7:].strip()
            self.agent_title = 'Local File Search'
            self.agent_color = '#FFFF00'
            self.last_command = user_input
            self.last_output = f'[bold yellow]🔍 Searching database for:[/bold yellow] {query}...\n'
            self.update_chat_panel()
            results_text = semantic_search(query)
            self.last_output = f'\n{results_text}\n'
            self.update_chat_panel()
            return
        elif user_input.lower().startswith('look'):
            parts = user_input.split(maxsplit=2)
            delay = 0
            query = 'Describe what is on my screen and identify any obvious errors, code, or context.'
            if len(parts) > 1 and parts[1].isdigit():
                delay = int(parts[1])
                if len(parts) > 2:
                    query = parts[2]
            elif len(user_input[4:].strip()) > 0:
                query = user_input[4:].strip()
            self.agent_title = 'Omni-Sight'
            self.agent_color = '#FF00FF'
            if delay > 0:
                self.last_output = f'\n**👁️ Omni-Sight Active:** Capturing screen in {delay} seconds...\n'
            else:
                self.last_output = f'\n**👁️ Omni-Sight Active:** Capturing screen state...\n'
            self.update_chat_panel()
            self.run_vision_pipeline(query, delay)
            return
        elif user_input.lower().startswith('headless '):
            objective = user_input[9:].strip()
            self.agent_title = 'Headless Engine'
            self.agent_color = '#00FF00'
            self.last_output = f'\n[bold green]🌐 Headless Engine Active:[/bold green] Initializing Playwright environment...\n'
            self.update_chat_panel()
            self.run_automation_pipeline(objective)
            return
        elif user_input.lower().strip() == 'galaxy':
            self.agent_title = 'Data Galaxy Engine'
            self.last_output = '\n[bold cyan]🔭 Building the Data Galaxy...[/bold cyan]\nMapping vector spaces. Please wait.'
            self.update_chat_panel()
            success = build_galaxy()
            if success:
                self.app.push_screen(GalaxyScreen())
            else:
                self.last_output = '\n[red]Failed to build Data Galaxy. Not enough files.[/red]\n'
                self.update_chat_panel()
            return
        elif user_input.lower().startswith('rewind '):
            target_file = user_input[7:].strip()
            self.agent_title = 'Chronos Engine'
            self.agent_color = '#0088FF'
            diff_result = rollback_file(target_file)
            self.last_output = f'\n[bold blue]⏳ Chronos Rewind Executed:[/bold blue]\n{diff_result}\n'
            self.update_chat_panel()
            return
        elif user_input.lower().strip() == 'map core':
            from ast_graph.ui import MapScreen
            self.agent_title = 'System Cartographer'
            self.last_output = '\n[bold cyan]🗺️ Rendering Abstract Syntax Tree...[/bold cyan]\n'
            self.push_screen(MapScreen())
            self.update_chat_panel()
            return
        elif user_input.lower().startswith('stock '):
            ticker = user_input[6:].strip().upper()
            from stock_market.mpl_ui import launch_stock_window
            self.agent_title = 'Wall Street Engine'
            self.last_output = f'\n[bold green]📈 Launching native charting engine for {ticker}...[/bold green]\n'
            self.update_chat_panel()
            with self.suspend():
                launch_stock_window(ticker)
            return
        if user_input:
            self.process_request(user_input)
    def save_journal_entry(self, message: str):
        self.last_output += '\n[dim cyan]> *Encrypting and saving to Lightning Journal...*[/dim cyan]\n'
        self.update_chat_panel()
        self.process_journal_async(message)
    @work(thread=True)
    def process_journal_async(self, message: str):
        prompt = 'Read the following journal entry and output EXACTLY ONE category tag enclosed in brackets. Choose from: [Academics], [Hardware], [Milestone], [Reflection]. Output absolutely nothing else.'
        try:
            response = client.chat.send(model=os.environ.get('AGENTIC_OS_MODEL', 'openrouter:free'), messages=[{'role': 'system', 'content': prompt}, {'role': 'user', 'content': message}], stream=False)
            tag = response.choices[0].message.content.strip()
            if not tag.startswith('['):
                tag = '[Reflection]'
        except Exception:
            tag = '[Reflection]'
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        journal_str = f'* {timestamp} - {tag}: {message}\n'
        with open(os.path.join(BASE_DIR, 'JOURNAL.md'), 'a', encoding='utf-8') as f:
            f.write(journal_str)
        safe_tag = tag.replace('[', '\\[')
        success_msg = f'[dim green]> ✔ Journal entry securely logged under {safe_tag}[/dim green]\n'
        def display_success():
            self.last_output += success_msg
            self.update_chat_panel()
        self.call_from_thread(display_success)
    @work(thread=True)
    def launch_browser(self, url: str):
        markdown_string = fetch_and_clean_html(url, client)
        def mount_screen():
            self.push_screen(BrowserScreen(markdown_string))
        self.call_from_thread(mount_screen)
    def _set_output(self, text):
        self.last_output = text
        self.call_from_thread(self.update_chat_panel)
    def _append_output(self, text):
        self.last_output += text
        self.call_from_thread(self.update_chat_panel)
    @work(thread=True)
    def generate_quiz(self, topic: str):
        prompt = f'Generate a single, difficult multiple-choice question about: {topic}. You MUST return strict JSON matching this schema exactly:\n{{"question": "...", "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}}, "correct": "<A, B, C, or D>", "explanation": "..."}}\nCRITICAL: Randomize which letter is the correct answer. Do NOT always make it A.\nReturn ONLY the JSON string. Do not use markdown blocks like ```json.'
        try:
            response = client.chat.send(model=os.environ.get('AGENTIC_OS_MODEL', 'openrouter:free'), messages=[{'role': 'user', 'content': prompt}], stream=False)
            raw = response.choices[0].message.content.strip()
            if raw.startswith('```json'):
                raw = raw[7:-3].strip()
            elif raw.startswith('```'):
                raw = raw[3:-3].strip()
            data = json.loads(raw)
            self.quiz_correct_answer = data['correct']
            self.quiz_explanation = data['explanation']
            def mount_quiz():
                options_text = f"[bold]A)[/bold] {data['options']['A']}\n[bold]B)[/bold] {data['options']['B']}\n[bold]C)[/bold] {data['options']['C']}\n[bold]D)[/bold] {data['options']['D']}"
                self.last_output += f"\n[bold #FFFF00]🧠 QUIZ TIME[/bold #FFFF00]\n{data['question']}\n\n{options_text}\n"
                self.update_chat_panel()
                try:
                    old = self.query_one('#quiz_buttons')
                    old.remove()
                except Exception:
                    pass
                container = Horizontal(Button('A', id='quiz_btn_A', name='A', variant='primary'), Button('B', id='quiz_btn_B', name='B', variant='primary'), Button('C', id='quiz_btn_C', name='C', variant='primary'), Button('D', id='quiz_btn_D', name='D', variant='primary'), id='quiz_buttons')
                self.query_one('#chat_scroll').mount(container)
                container.scroll_visible()
            self.call_from_thread(mount_quiz)
        except Exception as e:
            def show_err():
                self.last_output += f'\n[bold red]Quiz generation failed: {e}[/bold red]\n'
                self.update_chat_panel()
            self.call_from_thread(show_err)
    @on(Button.Pressed)
    def on_quiz_button_pressed(self, event: Button.Pressed):
        if event.button.id and event.button.id.startswith('quiz_btn_'):
            selected = event.button.name
            try:
                container = self.query_one('#quiz_buttons')
                container.remove()
            except Exception:
                pass
            if selected == getattr(self, 'quiz_correct_answer', ''):
                result_msg = f'\n[bold green]CORRECT![/bold green] You selected {selected}.\n[dim]{self.quiz_explanation}[/dim]\n'
            else:
                result_msg = f"\n[bold red]INCORRECT![/bold red] You selected {selected}. The correct answer was {getattr(self, 'quiz_correct_answer', '')}.\n[dim]{getattr(self, 'quiz_explanation', '')}[/dim]\n"
            self.last_output += result_msg
            self.update_chat_panel()
    @on(Button.Pressed, '#lofi_play')
    def resume_lofi(self, event):
        self.audio_system.play()
    @on(Button.Pressed, '#lofi_pause')
    def pause_lofi(self, event):
        self.audio_system.pause()
    @on(Button.Pressed, '#lofi_stop')
    def stop_lofi(self, event):
        self.audio_system.stop()
    @work(thread=True)
    def fetch_news(self):
        import urllib.request
        import xml.etree.ElementTree as ET
        def fetch_category(url):
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            try:
                with urllib.request.urlopen(req, timeout=5) as response:
                    root = ET.fromstring(response.read())
                    items = root.findall('.//item')[:3]
                    return [item.find('title').text for item in items]
            except Exception:
                return ['Headline unavailable']
        world = fetch_category('https://news.google.com/rss/headlines/section/topic/WORLD')
        local = fetch_category('https://news.google.com/rss/headlines/section/geo/Global')
        sports = fetch_category('https://news.google.com/rss/headlines/section/topic/SPORTS')
        formatted = []
        formatted.append('[bold #38BDF8]🌍 WORLD NEWS[/bold #38BDF8]')
        for title in world:
            formatted.append(f'[#BAE6FD]• {title}[/#BAE6FD]')
        formatted.append('')
        formatted.append('[bold #F472B6]📍 LOCAL NEWS[/bold #F472B6]')
        for title in local:
            formatted.append(f'[#FBCFE8]• {title}[/#FBCFE8]')
        formatted.append('')
        formatted.append('[bold #A78BFA]🏆 SPORTS[/bold #A78BFA]')
        for title in sports:
            formatted.append(f'[#DDD6FE]• {title}[/#DDD6FE]')
        final_markup = '\n'.join(formatted)
        def update_ui():
            try:
                self.query_one('#news_panel', Static).update(final_markup)
            except Exception:
                pass
        self.call_from_thread(update_ui)
    def start_focus_mode(self, minutes: int):
        self.remaining_focus_secs = minutes * 60
        self.query_one('#news_panel', Static).add_class('hidden')
        self.query_one('#focus_panel', Static).remove_class('hidden')
        self.last_output += f'\n[bold #FF00FF]🎯 Focus Mode Activated — {minutes} min. Distractions suppressed.[/bold #FF00FF]\n'
        self.update_chat_panel()
        if self.focus_timer is not None:
            self.focus_timer.stop()
        self.focus_timer = self.set_interval(1.0, self.tick_focus)
    def tick_focus(self):
        if self.remaining_focus_secs <= 0:
            self.focus_timer.stop()
            self.focus_timer = None
            self.query_one('#focus_panel', Static).add_class('hidden')
            self.query_one('#news_panel', Static).remove_class('hidden')
            self.last_output += '\n[bold #00FF00]✅ Focus Session Complete! Welcome back.[/bold #00FF00]\n'
            self.update_chat_panel()
            return
        mins, secs = divmod(self.remaining_focus_secs, 60)
        if self.remaining_focus_secs < 60:
            clock_str = f'[bold #FF0055]⏱ {mins:02d}:{secs:02d}[/bold #FF0055]'
        else:
            clock_str = f'[bold #FF00FF]⏱ {mins:02d}:{secs:02d}[/bold #FF00FF]'
        self.query_one('#focus_panel', Static).update(f'🎯 FOCUS MODE\n\n{clock_str}\n\n[dim]Stay locked in.[/dim]')
        self.remaining_focus_secs -= 1
    @work(thread=True)
    def process_request(self, user_input: str):
        current_dir = os.getcwd()
        visible_files = ', '.join(os.listdir(current_dir)[:20])
        recent_history = json.dumps(self.system_memory[-5:], indent=2)
        intent_category = route_intent(user_input, client)
        command_run = ''
        stdout_val = ''
        stderr_val = ''
        returncode = 0
        if 'TERMINAL' in intent_category:
            auto_checkpoint_dir(os.getcwd())
            res = execute_terminal_agent(user_input, current_dir, visible_files, recent_history, client, self._append_output)
            self.agent_title = res['agent_title']
            self.agent_color = res['agent_color']
            self.last_command = res['command']
            self.last_output = res['output']
            if res['new_dir'] and os.path.isdir(res['new_dir']) and (os.getcwd() != res['new_dir']):
                os.chdir(res['new_dir'])
            command_run = res['command']
            stdout_val = res['stdout']
            stderr_val = res['stderr']
            returncode = res['returncode']
        elif 'CONVERSATIONAL' in intent_category:
            self.agent_title = 'Conversational Agent'
            self.agent_color = '#FF00FF'
            self.last_command = user_input
            self.last_output = ''
            self.call_from_thread(self.update_chat_panel)
            res = stream_conversational_agent(user_input, client, self._append_output, self.system_memory)
            command_run = res['command']
            stdout_val = res['output']
        elif 'WEB' in intent_category:
            self.agent_title = 'Web Agent'
            self.agent_color = '#FFFF00'
            self.last_command = f'Web Search: Initiated...'
            res = stream_web_agent(user_input, client, self._set_output, self._append_output)
            self.last_command = res['command']
            command_run = res['command']
            stdout_val = res['output']
        else:
            self.agent_title = 'System Error'
            self.agent_color = '#FF0055'
            self.last_command = 'Routing Error'
            self.last_output = 'The Cognitive Router returned an invalid category.'
            command_run = 'Routing Error'
            stdout_val = self.last_output
        session_log = {'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'user_intent': user_input, 'generated_command': command_run, 'stdout': stdout_val if returncode == 0 else '', 'stderr': stderr_val if returncode != 0 else ''}
        self.system_memory.append(session_log)
        with open(MEMORY_FILE, 'w') as file:
            json.dump(self.system_memory, file, indent=4)
        self.call_from_thread(self.update_chat_panel)
    @work(thread=True)
    def run_voice_pipeline(self):
        try:
            wav_path = record_scratch_audio()
            text_result = transcribe_wav(wav_path)
            def update_ui():
                self.last_output = f'\n[bold green]✔ Transcribed:[/bold green] {text_result}\n'
                self.update_chat_panel()
                self.query_one(Input).value = text_result
            self.call_from_thread(update_ui)
        except Exception as e:
            def show_error():
                self.last_output = f'\n[bold red]✘ Voice Error:[/bold red] {e}\n'
                self.update_chat_panel()
            self.call_from_thread(show_error)
    @work(thread=True)
    def run_vision_pipeline(self, query: str, delay: int):
        try:
            img_path = capture_screen(delay=delay)
            context = get_recent_code_context(BASE_DIR)
            text_result = analyze_image(img_path, client, query, code_context=context)
            def update_ui():
                self.last_output += f'\n**✔ Vision Analysis:**\n\n{text_result}\n'
                self.update_chat_panel()
            self.call_from_thread(update_ui)
        except Exception as e:
            def show_error():
                self.last_output += f'\n**✘ Omni-Sight Error:**\n\n{e}\n'
                self.update_chat_panel()
            self.call_from_thread(show_error)
    @work(thread=True)
    def run_automation_pipeline(self, objective: str):
        try:
            def _append_output(text):
                self.last_output += text
                self.call_from_thread(self.update_chat_panel)
            result = execute_web_automation(objective, client, _append_output)
            def finalize_ui():
                self.last_output += f"\n[bold cyan]✔ Task Complete:[/bold cyan] {result['output']}\n"
                self.update_chat_panel()
            self.call_from_thread(finalize_ui)
        except Exception as e:
            def show_error():
                self.last_output += f'\n[bold red]✘ Headless Error:[/bold red] {e}\n'
                self.update_chat_panel()
            self.call_from_thread(show_error)
if __name__ == '__main__':
    from rich.console import Console
    console = Console()
    print('Booting Knowledge Vault...')
    import chromadb
    _client = chromadb.PersistentClient(path='./physics_db')
    _collection = _client.get_or_create_collection(name='physics_vault')
    _collection.upsert(documents=['warmup'], ids=['__warmup__'])
    print('Knowledge Vault online.')
    app = KernelOS()
    app.run()
    console.print('\n[dim cyan]System successfully terminated. Goodbye![/dim cyan]')
