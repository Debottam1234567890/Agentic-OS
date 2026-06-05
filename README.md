<div align="center">
  <h1>🌌 Agentic OS</h1>
  <p><strong>A Next-Generation AI Command Center built in Textual</strong></p>
</div>

<br>

Welcome to **Agentic OS**—a terminal-based operating system powered by multi-modal AI agents. Engineered to be completely autonomous, highly resilient, and beautifully designed with sleek cyberpunk/hacker aesthetics. 

Agentic OS provides a centralized dashboard featuring a built-in terminal agent, web researcher, headless browser automator, computer vision analyzer, voice transcriber, and live data telemetry.

## ✨ Core Features

*   🖥️ **The Terminal Agent**: An autonomous coder running in your `sandbox/` directory. It can write Python scripts, build architecture maps, patch files, and execute bash commands dynamically.
*   🌐 **The Web Agent**: Fetches and synthesizes information directly from DuckDuckGo and proxy APIs to answer questions grounded in real-world data without hallucinations.
*   🎭 **Headless Browser Daemon**: Uses Playwright to autonomously navigate websites, click buttons, extract data, and fill forms.
*   👁️ **Vision & Camera**: Includes integrated computer vision using OpenCV to take snapshots, analyze screen states, or read physical documents through your webcam.
*   🎙️ **Voice Control**: Hit the shortcut, speak your command, and Agentic OS will transcribe the audio (via a local Whisper or fast API fallback) and execute your instruction.
*   ⏱️ **Chronos Snapshot & Rewind**: An automatic Git-like snapshot engine. Did an agent mess up your codebase? Just type `rewind` to instantly restore the `sandbox/` state to 5 minutes ago.
*   📈 **Data Galaxy & Market Telemetry**: Features interactive visualizations of live data. Maps abstract syntax trees into node graphs or pulls live stock metrics.
*   📰 **Real-Time News Feed**: Uses `xml.etree.ElementTree` to scrape live Google News RSS feeds continuously without wasting API tokens.

---

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Debottam1234567890/Agentic-OS.git
   cd Agentic-OS
   ```

2. **Set up your Virtual Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

4. **API Keys:**
   Create a file called `api.txt` in the root folder and paste your OpenRouter/Proxy API key.

5. **Boot the OS:**
   ```bash
   python3 kernel.py
   ```

---

## 🛠️ Architecture Overview

The system is built entirely on the **Textual** TUI framework, offering native macOS-level performance straight from the terminal. 

The `kernel.py` acts as the main execution loop. It intercepts all user commands, parses the intent using `logic_router.py`, and dispatches the instruction to one of several specialized agents.

*   `agents/`: Contains the conversational AI, the terminal code-execution loop, and the RAG (Retrieval-Augmented Generation) agent.
*   `browser/`: Handles raw HTML fetching and DOM parsing.
*   `headless/`: Implements the Playwright daemon for true browser interaction.
*   `chronos/`: The file-watching subsystem that zips your sandbox state on every file mutation.
*   `vision/ & voice/`: Multi-modal bridges to local hardware (camera and mic).

> **Note:** The codebase has been aggressively minified (stripped of comments and blank lines) to optimize read speeds for LLM operations. 

---

## 🎨 UI & Aesthetics

Agentic OS was explicitly designed to *wow*.
*   **Vibrant Syntax Highlighting:** Utilizes Rich for beautiful markdown rendering.
*   **Dynamic Telemetry:** The sidebar features live progress bars for CPU, RAM, and Disk space alongside the live news.
*   **Custom Styling:** Incorporates sleek dark modes, HSL tailored neon colors (`#A78BFA` purples, `#38BDF8` blues), and dynamic animations. 

---

## 📜 License & Acknowledgements

Created as an experimental foray into local, agent-driven operating systems. Built using Python, Textual, Rich, Playwright, and Pyfiglet.

**User Safety:** The terminal agent is hard-coded to *only* execute modifications inside the `/sandbox` folder to prevent accidental system destruction.
