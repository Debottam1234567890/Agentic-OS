import os
import subprocess
import json
import ast
from prompts import TERMINAL_AGENT_PROMPT

def map_architecture(current_dir: str, target_path: str='.'):
    sandbox_dir = current_dir
    guardrail_list = ['.git', '__pycache__', 'node_modules', '.venv', 'venv']
    architecture_map = []
    if target_path == '.':
        target_path = sandbox_dir
    elif not os.path.isabs(target_path):
        target_path = os.path.join(sandbox_dir, target_path)
    for root, dirs, files in os.walk(target_path):
        for d in reversed(dirs):
            if d in guardrail_list:
                dirs.remove(d)
        for file_name in files:
            if not file_name.endswith('.py'):
                continue
            file_path = os.path.join(root, file_name)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception:
                continue
            try:
                syntax_tree = ast.parse(content)
            except SyntaxError:
                continue
            file_elements = []
            for node in syntax_tree.body:
                if isinstance(node, ast.ClassDef):
                    docstring = ast.get_docstring(node)
                    file_elements.append(f'Class: {node.name} - {docstring}')
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    docstring = ast.get_docstring(node)
                    file_elements.append(f'Function: {node.name} - {docstring}')
            if len(file_elements) > 0:
                header = f'### File: {file_path}'
                architecture_map.append(header)
                architecture_map.extend(file_elements)
                architecture_map.append('')
    final_output = '\n'.join(architecture_map)
    if not final_output.strip():
        return 'No Python architecture found.'
    return final_output
def write_file(current_dir, filename: str, content: str):
    sandbox_dir = current_dir
    file_path = os.path.join(sandbox_dir, filename) if not os.path.isabs(filename) else filename
    if not file_path.startswith(sandbox_dir):
        return 'Access Denied: Cannot write outside the sandbox.'
    try:
        with open(file_path, 'w') as file:
            file.write(content)
        return 'Success: File written to sandbox.'
    except Exception as e:
        return f'Error writing file: {str(e)}'
def read_file(current_dir, filename: str):
    sandbox_dir = current_dir
    file_path = os.path.join(sandbox_dir, filename) if not os.path.isabs(filename) else filename
    if not file_path.startswith(sandbox_dir):
        return 'Access Denied: Cannot read outside the sandbox.'
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        return f'Error: File not found or cannot be read. {str(e)}'
def execute_bash(current_dir, command):
    sandbox_dir = current_dir
    if command.startswith('python3 ') or command.startswith('python '):
        filename = command.split(' ')[1]
        compile_process = subprocess.run(f"cd '{sandbox_dir}' && python3 -m py_compile {filename}", shell=True, capture_output=True, text=True)
        if compile_process.returncode != 0:
            return f'SYNTAX ERROR CAUGHT BY COMPILER:\n{compile_process.stderr}'
    tracked_command = f"cd '{sandbox_dir}' && {command}"
    process = subprocess.run(tracked_command, shell=True, capture_output=True, text=True)
    if process.returncode == 0:
        return f'STDOUT:\n{process.stdout}' if process.stdout else 'Command executed successfully with no output.'
    else:
        return f'STDERR:\n{process.stderr}'
def search_codebase(current_dir, query: str):
    sandbox_dir = current_dir
    guardrail_list = ['.git', '__pycache__', 'node_modules', '.venv', 'venv']
    match_results = []
    for root, dirs, files in os.walk(sandbox_dir):
        for d in reversed(dirs):
            if d in guardrail_list:
                dirs.remove(d)
        for f in files:
            file_path = os.path.join(root, f)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    for line_number, line in enumerate(file, start=1):
                        if query in line:
                            stripped_line = line.lstrip()
                            formatted_string = f'[File: {file_path}, Line: {line_number}] {stripped_line}'
                            match_results.append(formatted_string)
            except Exception:
                continue
    if len(match_results) == 0:
        return f"No matches found for '{query}' in the codebase."
    return '\n'.join(match_results)
def patch_file(current_dir, file_path: str, start_line: int, end_line: int, replacement_code: str):
    sandbox_dir = current_dir
    if not os.path.isabs(file_path):
        file_path = os.path.join(sandbox_dir, file_path)
    if not file_path.startswith(sandbox_dir):
        return 'Access Denied: Cannot modify files outside the sandbox.'
    guardrail_list = ['.git', '__pycache__', 'node_modules', '.venv', 'venv']
    path_parts = file_path.split(os.sep)
    for part in path_parts:
        if part in guardrail_list:
            return 'Access Denied: Cannot modify protected system files.'
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_lines = f.readlines()
    except FileNotFoundError:
        return f"Error: The file '{file_path}' does not exist."
    except Exception as e:
        return f'Error reading file: {str(e)}'
    start_index = start_line - 1
    end_index = end_line
    formatted_replacement = [line + '\n' for line in replacement_code.split('\n')]
    modified_lines = file_lines[:start_index] + formatted_replacement + file_lines[end_index:]
    assembled_string = ''.join(modified_lines)
    try:
        compile(assembled_string, file_path, 'exec')
    except SyntaxError as e:
        return f'Syntax Error Caught Before Save: {e}'
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(modified_lines)
    return f'Success: File patched from line {start_line} to {end_line}.'
def execute_terminal_agent(user_input: str, current_dir: str, visible_files: str, recent_history: str, client, update_callback) -> dict:
    sandbox_dir = current_dir
    messages = [{'role': 'system', 'content': TERMINAL_AGENT_PROMPT + f'\n\nCurrent Directory: {current_dir}\nVisible Files: {visible_files}\nRecent System History: \n{recent_history}'}, {'role': 'user', 'content': user_input}]
    step_counter = 0
    final_message = 'Task aborted: Maximum reasoning steps reached.'
    last_execution_output = 'No commands were executed.'
    while step_counter < 40:
        if step_counter <= 10:
            model=os.environ.get('AGENTIC_OS_MODEL', 'openrouter/free')
            update_callback(f'\n[dim cyan]*[Swarm Level 1: Qwen Active]*[/dim cyan]\n')
        elif step_counter <= 33:
            model=os.environ.get('AGENTIC_OS_MODEL', 'openrouter/free')
            update_callback(f'\n[bold green]*[Swarm Level 2: Gemini Active]*[/bold green]\n')
        else:
            model=os.environ.get('AGENTIC_OS_MODEL', 'openrouter/free')
            update_callback(f'\n[bold yellow]*[Swarm Level 3: Claude Active]*[/bold yellow]\n')
        response = client.chat.send(model=model, messages=messages, stream=False)
        raw_response = response.choices[0].message.content.strip()
        if raw_response.startswith('```json'):
            raw_response = raw_response[7:-3].strip()
        elif raw_response.startswith('```'):
            raw_response = raw_response[3:-3].strip()
        try:
            command_dict = json.loads(raw_response)
        except json.JSONDecodeError as e:
            messages.append({'role': 'assistant', 'content': raw_response})
            messages.append({'role': 'user', 'content': f'TOOL OUTPUT:\nJSON Parsing Error. You MUST return valid JSON. Do not use markdown.'})
            step_counter += 1
            continue
        thought = command_dict.get('thought', 'Processing...')
        update_callback(f'\n> *{thought}*...\n')
        messages.append({'role': 'assistant', 'content': raw_response})
        tool_name = command_dict.get('tool_name', '').lower()
        tool_args = command_dict.get('tool_args', {})
        if tool_name == 'task_complete':
            final_message = tool_args.get('final_message', 'Task completed autonomously.')
            break
        tool_result = ''
        if tool_name == 'write_file':
            tool_result = write_file(current_dir, tool_args.get('filename', ''), tool_args.get('content', ''))
        elif tool_name == 'read_file':
            tool_result = read_file(current_dir, tool_args.get('filename', ''))
        elif tool_name == 'execute_bash':
            tool_result = execute_bash(current_dir, tool_args.get('command', ''))
            last_execution_output = tool_result
        elif tool_name == 'map_architecture':
            tool_result = map_architecture(current_dir, tool_args.get('target_path', '.'))
        elif tool_name == 'search_codebase':
            tool_result = search_codebase(current_dir, tool_args.get('query', ''))
        elif tool_name == 'patch_file':
            try:
                tool_result = patch_file(current_dir, tool_args.get('file_path', ''), int(tool_args.get('start_line', 0)), int(tool_args.get('end_line', 0)), tool_args.get('replacement_code', ''))
            except Exception as e:
                tool_result = f'Execution Error in patch_file: {str(e)}'
        else:
            tool_result = f"Error: Unknown tool '{tool_name}'. Available tools: write_file, read_file, execute_bash, map_architecture, search_codebase, patch_file, task_complete"
        messages.append({'role': 'user', 'content': f'TOOL OUTPUT:\n{tool_result}'})
        step_counter += 1
    return {'agent_title': '', 'agent_color': '#00FFFF', 'command': 'Swarm Execution Sequence', 'output': f'{final_message}\n\n[dim cyan]Raw Terminal Output:[/dim cyan]\n[white]{last_execution_output}[/white]', 'new_dir': current_dir, 'stdout': final_message, 'stderr': '', 'returncode': 0}
