import os
import subprocess
from prompts import TERMINAL_AGENT_PROMPT

def execute_terminal_agent(user_input: str, current_dir: str, visible_files: str, recent_history: str, client) -> dict:
    """Handles bash generation, execution, and error correction."""
    response = client.chat.send(
        model="qwen/qwen3-32b",
        messages=[
            {"role": "system", "content": TERMINAL_AGENT_PROMPT + f"\n\nCurrent Directory: {current_dir}\nVisible Files: {visible_files}\nRecent System History: \n{recent_history}"},
            {"role": "user", "content": user_input}
        ],
        stream=False,
    )
    command = response.choices[0].message.content.strip()
    
    tracked_command = f"{command} && pwd"
    process = subprocess.run(tracked_command, shell=True, capture_output=True, text=True)
    
    if process.returncode == 0:
        output_lines = process.stdout.strip().split('\n')
        new_dir = output_lines[-1] 
        actual_output = '\n'.join(output_lines[:-1])
        
        return {
            "agent_title": "Terminal Agent",
            "agent_color": "#00FFFF",  # Cyan glow
            "command": command,
            "output": actual_output if actual_output else "Command executed successfully with no output.",
            "new_dir": new_dir,
            "stdout": process.stdout,
            "stderr": process.stderr,
            "returncode": 0
        }
    else:
        FIXER_PROMPT = f"The user wanted to: '{user_input}'. You generated the command: '{command}'. It failed with this exact error: '{process.stderr}'. Provide ONLY the corrected macOS terminal command to fix this. Do not include markdown formatting or conversational text"
        fix_response = client.chat.send(
            model="qwen/qwen3-32b",
            messages=[{"role": "system", "content": FIXER_PROMPT}],
            stream=False
        )
        new_command = fix_response.choices[0].message.content.strip()
        tracked_fix = f"{new_command} && pwd"
        fix_process = subprocess.run(tracked_fix, shell=True, capture_output=True, text=True)
        
        if fix_process.returncode == 0:
            output_lines = fix_process.stdout.strip().split('\n')
            new_dir = output_lines[-1]
            actual_output = '\n'.join(output_lines[:-1])
            return {
                "agent_title": "Terminal Agent",
                "agent_color": "#00FFFF",
                "command": new_command,
                "output": f"[{'#00FFFF'}]Attempting Corrected Command[/{'#00FFFF'}] [white]{new_command}[/white]\n" + (actual_output if actual_output else "Autonomous correction executed successfully with no output."),
                "new_dir": new_dir,
                "stdout": fix_process.stdout,
                "stderr": fix_process.stderr,
                "returncode": 0
            }
        else:
            return {
                "agent_title": "Terminal Agent",
                "agent_color": "#00FFFF",
                "command": f"{command} (failed)",
                "output": f"Command Failed: {process.stderr.strip()}\nAutonomous Correction Failed: {fix_process.stderr.strip()}",
                "new_dir": None,
                "stdout": fix_process.stdout,
                "stderr": fix_process.stderr,
                "returncode": fix_process.returncode
            }
