# Agentic OS — Technical Manual & Feature Reference

Welcome to the **Agentic OS**! This is a comprehensive terminal-based operating environment built using Python, `Textual`, and a swarm of autonomous LLM agents. 

The OS acts as a centralized dashboard for productivity, system management, knowledge retrieval, and AI interaction.

---

## 1. System Commands (Direct execution)

These commands bypass the LLM Logic Router and are executed immediately by the OS Kernel.

- **`exit`, `quit`, `bye`, `terminate`, `shutdown`**
  Safely shuts down the Agentic OS and kills background processes.
- **`log <message>`**
  Encrypts and saves the message to the Lightning Journal (`.os_memory.json`). An asynchronous background LLM process analyzes the log and tags it automatically with one of: `[Academics]`, `[Hardware]`, `[Milestone]`, or `[Reflection]`.
- **`browse <url>`**
  Invokes the internal Browser Engine. It fetches the URL, strips away ads/HTML/JS, and opens a clean, full-screen Markdown Viewer in your terminal.
- **`lofi start`**
  Mounts the Media Controller widget to your sidebar and spawns a background `afplay` subprocess to play `lofi.mp3`. You can pause/stop it via the UI buttons.
- **`tasks`**
  Launches the interactive Kanban Board UI to manage your current workflow.
- **`listen`**
  Activates Voice Input Mode. Records 5 seconds of audio directly from your microphone and passes it to the Google Speech Recognition API to transcribe into text.
- **`search <query>`**
  Executes a Hybrid RAG Search across your entire codebase, returning the Top 10 most relevant file snippets with a combination of BM25 (keyword) and ChromaDB (semantic) matching.
- **`vision [delay_in_seconds] <query>`** *(NEW)*
  Activates the Omni-Sight Vision Engine. Takes a screenshot of your primary display (with an optional timer) and uses a Multimodal Vision LLM to analyze the screen and answer your query natively in the OS.
- **`headless <objective>`** *(NEW)*
  Activates the Autonomous Headless Browser Agent. Boots a Playwright instance with anti-bot stealth technologies to navigate complex websites, solve popups, click elements, and extract structured data autonomously based on your objective.
- **`rewind <filename>`** *(NEW)*
  Triggers the Chronos Time-Travel Engine. Pulls the most recent backup of the file from the `.chronos_vault`, instantly rendering a color-coded unified diff in the terminal, and rolling the file back to its previous state.

---

## 2. Cognitive Logic Router

If you type anything that is *not* a system command (e.g., "What is a neural network?" or "List all files in this directory"), the input is sent to the **Logic Router** (`logic_router.py`).

The Router uses an LLM to classify your intent into one of three distinct agent pipelines:

### ⚡ Terminal Agent (`TERMINAL`)
If you ask the OS to manipulate files, run scripts, or check system stats, the Terminal Agent takes over. It has full read/write access to your machine. It generates sandboxed terminal commands (like `ls`, `cat`, or python scripts), executes them natively via `subprocess`, and evaluates the `stdout/stderr` before returning an answer. *Note: The Chronos Engine automatically snapshots your sandbox files before every execution to protect against accidental damage.*

### 🧠 Conversational Agent (`CONVERSATIONAL`)
If you ask general knowledge, physics, or coding questions, the Conversational Agent handles it. It streams Markdown-formatted responses directly to your chat interface. It also has access to the **RAG Agent** pipeline (`rag_agent.py`) to retrieve domain-specific context from the `physics_db` if needed.

### 🌐 Web Agent (`WEB`)
If you ask about live, up-to-date events (e.g., "What is the weather today?"), the Web Agent takes over. It uses `BeautifulSoup` to scrape live internet data, synthesizes the HTML content, and formats it into a clean summary.

---

## 3. Core Subsystems

The OS is broken down into several modular directories, each handling a specific feature suite:

### 📋 Kanban Subsystem (`kanban/`)
- **Persistent Storage**: Tasks are saved locally to `tasks.json`.
- **Interactive UI**: A full-screen Textual overlay with 3 columns (TODO, DOING, DONE).
- **Keyboard Navigation**: Press `h` to move a task left, `l` to move it right, and `d` or `Backspace` to delete it. Press `a` to open the input bar for a new task.

### 🔍 Neural Find Engine (`neural_find/`)
- **Indexer (`indexer.py`)**: Crawls the workspace to build a local vector database (`ChromaDB`) for semantic meaning, AND a `keyword_index.json` for exact word mapping.
- **Hybrid Searcher (`searcher.py`)**: Implements an industry-standard dual-engine search. It calculates BM25 scores (with bonuses for exact filename matches) and Semantic Vector distances, then merges them perfectly using **Reciprocal Rank Fusion (RRF)**.

### 🎧 Media Player (`media_player/`)
- **Audio Controller**: Manages daemon threads for seamless background music that survives UI state changes without blocking the terminal.
- **Widget**: Injects live playback controls (Play, Pause, Stop) directly into the Textual DOM.

### 🎤 Voice Pipeline (`voice/`)
- **Microphone Daemon**: Interfaces with system audio hardware via the `sounddevice` library to dump scratch WAV files.
- **Transcriber**: Ingests raw audio payloads and translates them into clean string text using external speech APIs.

### 🌍 Internal Browser (`browser/`)
- **Engine**: Replaces the need for external tools like Chrome or Safari by fetching live DOM trees and reducing them to terminal-friendly markdown.
- **Viewer**: A specialized `Textual.Screen` overlay for reading long-form web content efficiently.

### 🤖 Automation Agent (`headless/`) *(NEW)*
- **Engine**: A robust Playwright-powered browser hidden in the background (`--headless=new`).
- **Stealth**: Bypasses Cloudflare, DataDome, and advanced bot protections using `playwright-stealth`.
- **ReAct Loop**: A 50-step autonomous orchestration engine that fetches Node IDs, scrolls, clicks, and extracts data strictly using JSON commands.

### 👁️ Vision Engine (`vision/`) *(NEW)*
- **Camera Daemon**: Interfaces directly with macOS `screencapture` utility.
- **Analyzer**: Marshals Base64 image payloads over to multimodal LLMs to provide real-time spatial awareness of the user's desktop.

### ⏳ Chronos Engine (`chronos/`) *(NEW)*
- **Snapshot Daemon**: A background `watchdog` process tracking all filesystem edits in real-time natively in python.
- **Vault**: Silently creates time-stamped `.bak` files inside a hidden `.chronos_vault/` index.
- **Rewind Engine**: Resolves the target file, iterates backward through time, diffs the edits dynamically, and restores the previous state natively into the OS without git.

---

## 4. UI / UX Features

- **Live News Feed**: An automated sidebar that color-codes incoming streams into `[WORLD]`, `[LOCAL]`, and `[SPORTS]` buckets.
- **Hardware Telemetry**: Displays real-time CPU, RAM, and Disk usage via the `psutil` library.
- **Focus Mode**: Hides non-essential sidebar panels to present a minimalist countdown timer for deep work sessions.
- **Safe Markdown Rendering**: Fully escapes system-injected raw code to prevent Rich markup parser crashes (preventing `MarkupError`s).
