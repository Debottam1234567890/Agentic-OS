# yo whats up 🌌 Agentic OS 🌌

ok so tbh i just wanted a terminal that actually DOES stuff instead of me typing forever lol. 

Agentic OS is my next gen ai command center built in Textual!! basically it has all these sick ai agents that run directly in ur terminal and see ur screen n stuff

## omg the features 🤯
dude literally this thing is packed
- **Terminal Agent:** an autonomous coding bot that writes python, fixes bugs n patches files right in ur folder.
- **Web Agent (`browse <url>`):** it actually browses the web using duckduckgo and proxy apis so it doesnt hallucinate 
- **Headless Browser (`headless <task>`):** invisible playwright bot that clicks buttons and fills out forms for u LMAO
- **Omni-Sight (`look`):** takes a snap of ur screen to debug stuff physically using computer vision !!
- **Voice Agent (`listen`):** talk to it and whisper transcribes everything u say and executes it
- **Conversational Agent:** just a chill bot for reasoning
- **RAG Search (`search`):** local semantic search over ur codebase using chromadb so u can chat w ur files

## extra crazy stuff i added
- **Chronos Snapshot (`rewind`):** basically if the ai bricks ur code u just type rewind and it goes back 5 mins like a time machine!!
- **Data Galaxy (`galaxy`):** builds a 3d map of ur syntax trees 
- **Wall street engine (`stock AAPL`):** pulls live stock charts right in the terminal
- **News feed:** live google news rss scrape

## how to run this bad boy 🚀
u gotta do this:
1. `git clone https://github.com/Debottam1234567890/Agentic-OS.git`
2. `cd Agentic-OS`
3. set up a venv cuz python will complain otherwise `python3 -m venv venv` and `source venv/bin/activate`
4. install my crazy deps: `pip install -r requirements.txt` and `playwright install`
5. FOR LINUX U NEED: `sudo apt-get update` then `sudo apt-get install -y portaudio19-dev` and `playwright install-deps` (if ur on mac just `brew install portaudio`)
6. get ur FREE api key from https://ai.hackclub.com and set it: `export OPENROUTER_API_KEY="ur-key-here"` or just paste it in a file called `api.txt` in the project folder
7. optionally pick a custom model: `export AGENTIC_OS_MODEL="google/gemini-3.5-flash"` (defaults to `nvidia/nemotron-3-nano-30b-a3b:free` if u leave it blank — its free!!)
8. start it up: `python3 kernel.py`

## architecture idk
everything is built on **Textual** TUI framework so its crazy fast. `kernel.py` intercepts ur cmds and routes them using `logic_router.py` to all the agents. 
ui looks super hacker-y with neon purples and blue dark mode 🎨 

**WARNING:** plz use a `sandbox/` folder cuz the ai might accidentally wipe ur system if u let it run wild LOL 😭

anyways hope u guys like it!!!
