import os
import subprocess
import json
from prompts import TERMINAL_AGENT_PROMPT

def write_file(current_dir, filename: str, content: str):
    file_path = os.path.join(current_dir, "sandbox", filename)
    try:
        with open(file_path, "w") as file:
            file.write(content)
        return "Success: File written to sandbox."
    except Exception as e:
        return f"Error writing file: {str(e)}"

def read_file(current_dir, filename: str):
    file_path = os.path.join(current_dir, "sandbox", filename)
    try:
        with open(file_path, "r") as file:
            return file.read()
    except Exception as e:
        return f"Error: File not found or cannot be read. {str(e)}"

def execute_bash(command):
    # Phase 72 Compiler Guardrail: Check the RAW command first
    if command.startswith("python3 ") or command.startswith("python "):
        filename = command.split(" ")[1]
        compile_process = subprocess.run(f"cd sandbox && python3 -m py_compile {filename}", shell=True, capture_output=True, text=True)
        if compile_process.returncode != 0:
            return f"SYNTAX ERROR CAUGHT BY COMPILER:\n{compile_process.stderr}"

    # Proceed to actual execution
    tracked_command = f"cd sandbox && {command}"
    process = subprocess.run(tracked_command, shell=True, capture_output=True, text=True)
    
    if process.returncode == 0:
        return f"STDOUT:\n{process.stdout}" if process.stdout else "Command executed successfully with no output."
    else:
        return f"STDERR:\n{process.stderr}"

# Phase 74: Added update_callback to the function signature
def execute_terminal_agent(user_input: str, current_dir: str, visible_files: str, recent_history: str, client, update_callback) -> dict:
    """Handles autonomous ReAct loop for writing, testing, and debugging code."""
    
    # Phase 69: Ensure Sandbox Exists
    os.makedirs(os.path.join(current_dir, "sandbox"), exist_ok=True)

    messages = [
        {"role": "system", "content": TERMINAL_AGENT_PROMPT + f"\n\nCurrent Directory: {current_dir}\nVisible Files: {visible_files}\nRecent System History: \n{recent_history}"},
        {"role": "user", "content": user_input}
    ]
    
    step_counter = 0
    final_message = "Task aborted: Maximum reasoning steps (5) reached."
    last_execution_output = "No commands were executed."

    while step_counter < 10:
        if step_counter <= 3:
            model = "qwen/qwen3-32b"
            update_callback(f"\n[dim cyan]*[Swarm Level 1: Qwen Active]*[/dim cyan]\n")
        elif step_counter <= 8:
            model = "google/gemini-2.5-pro"
            update_callback(f"\n[bold green]*[Swarm Level 2: Gemini Active]*[/bold green]\n")
        else:
            model = "anthropic/claude-opus-4.8"
            update_callback(f"\n[bold magenta]*[Swarm Level 3: Claude Active]*[/bold magenta]\n")
        response = client.chat.send(
            model=model,
            messages=messages,
            stream=False,
        )
        
        raw_response = response.choices[0].message.content.strip()
        
        # Defensive check in case the AI wraps the JSON in markdown blocks
        if raw_response.startswith("```json"):
            raw_response = raw_response[7:-3].strip()
        elif raw_response.startswith("```"):
            raw_response = raw_response[3:-3].strip()
            
        try:
            command_dict = json.loads(raw_response)
        except json.JSONDecodeError as e:
            # If AI messes up the JSON formatting, feed the error back so it fixes it!
            messages.append({"role": "assistant", "content": raw_response})
            messages.append({"role": "user", "content": f"TOOL OUTPUT:\nJSON Parsing Error. You MUST return valid JSON. Do not use markdown."})
            step_counter += 1
            continue

        # Phase 74: Stream the thought process to the Terminal UI
        thought = command_dict.get("thought", "Processing...")
        update_callback(f"\n> *{thought}*...\n")
        
        # Save the AI's action to the message history so it remembers what it just did
        messages.append({"role": "assistant", "content": raw_response})
        
        tool_name = command_dict.get("tool_name", "").lower()
        tool_args = command_dict.get("tool_args", {})
        
        # Check for exit condition
        if tool_name == "task_complete":
            final_message = tool_args.get("final_message", "Task completed autonomously.")
            break
        
        # Execute the requested tool
        tool_result = ""
        if tool_name == "write_file":
            tool_result = write_file(current_dir, tool_args.get("filename", ""), tool_args.get("content", ""))
        elif tool_name == "read_file":
            tool_result = read_file(current_dir, tool_args.get("filename", ""))
        elif tool_name == "execute_bash":
            tool_result = execute_bash(tool_args.get("command", ""))
            last_execution_output = tool_result
        else:
            tool_result = f"Error: Unknown tool '{tool_name}'. Available tools: write_file, read_file, execute_bash, task_complete."
            
        # The Feedback Loop: Send the tool's output back to the AI
        messages.append({"role": "user", "content": f"TOOL OUTPUT:\n{tool_result}"})
        
        step_counter += 1

    # Return final results back to kernel.py
    return {
        "agent_title": "",
        "agent_color": "#00FFFF",  
        "command": "Swarm Execution Sequence",
        "output": f"{final_message}\n\n[dim cyan]Raw Terminal Output:[/dim cyan]\n[white]{last_execution_output}[/white]",
        "new_dir": current_dir, # Directory doesn't change because we use the sandbox
        "stdout": final_message,
        "stderr": "",
        "returncode": 0
    }