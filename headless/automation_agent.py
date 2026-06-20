import os
import json
from headless.headless_daemon import HeadlessBrowser
AUTOMATION_PROMPT = 'You are a professional Web Automation Agent controlling a headless browser.\n\n## Available tools (output ONE JSON object per turn)\n{ "thought": "...", "tool": "<tool_name>", "args": {<tool_args>} }\n\n| Tool        | Args                              | Description |\n|-------------|-----------------------------------|-------------|\n| navigate    | {"url": "https://..."}            | Go to a URL directly. Use this to jump to known URLs. |\n| extract     | {}                                | Read the current page. Returns interactive elements with IDs and page text. |\n| click       | {"node_id": "5"}                  | Click element by its [ID] from the extract output. |\n| type        | {"node_id": "3", "text": "query"} | Type text into an input field by its [ID]. |\n| press_enter | {}                                | Press the Enter key (e.g. to submit a search form). |\n| scroll      | {"direction": "down" or "up"}     | Scroll the viewport to reveal more content. |\n| complete    | {"result": "The final answer"}    | Finish the task. You MUST put the extracted data in result. |\n\n## Critical rules\n1. ALWAYS call \'extract\' FIRST after every \'navigate\' or \'click\' to see what is on the new page.\n2. Use the numerical [ID] from extract output for click/type. NEVER guess CSS selectors.\n3. If the element you need is not visible, use \'scroll\' then \'extract\' again.\n4. \'type\' only fills the field. Use \'press_enter\' separately to submit.\n5. If a site blocks you, try navigating directly to the target URL instead of clicking through menus.\n6. For \'complete\', always include the actual data/text you extracted in the \'result\' field.\n7. Do NOT give up easily. Try alternative navigation paths, direct URLs, or search engines.\n'
def execute_web_automation(user_input: str, client, update_callback) -> dict:
    browser = HeadlessBrowser()
    browser.start()
    messages = [{'role': 'system', 'content': AUTOMATION_PROMPT}, {'role': 'user', 'content': user_input}]
    step_counter = 0
    final_output = {'output': 'Task failed to complete within step limits.'}
    try:
        while step_counter < 50:
            response = client.chat.send(model=os.environ.get('AGENTIC_OS_MODEL', 'openrouter/free'), messages=messages, max_tokens=5000, stream=False)
            raw_content = response.choices[0].message.content.strip()
            cleaned = raw_content
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.startswith('```'):
                cleaned = cleaned[3:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            action = None
            try:
                action = json.loads(cleaned)
            except json.JSONDecodeError:
                start = cleaned.find('{')
                end = cleaned.rfind('}')
                if start != -1 and end != -1 and (end > start):
                    try:
                        action = json.loads(cleaned[start:end + 1])
                    except json.JSONDecodeError:
                        pass
            if action is None:
                messages.append({'role': 'assistant', 'content': raw_content})
                messages.append({'role': 'user', 'content': 'ERROR: Your last response was not valid JSON. Output ONLY a single JSON object: {"thought": "...", "tool": "...", "args": {...}}'})
                step_counter += 1
                continue
            thought = action.get('thought', 'Thinking...')
            tool = action.get('tool', '')
            args = action.get('args', {})
            update_callback(f'\n> *{thought}*...\n')
            result = ''
            if tool == 'navigate':
                result = browser.navigate(args.get('url', ''))
            elif tool == 'extract':
                result = browser.get_dom_snapshot()
            elif tool == 'click':
                result = browser.click(str(args.get('node_id', '')))
            elif tool == 'type':
                result = browser.type_text(str(args.get('node_id', '')), args.get('text', ''))
            elif tool == 'press_enter':
                result = browser.press_enter()
            elif tool == 'scroll':
                result = browser.scroll(args.get('direction', 'down'))
            elif tool == 'complete':
                final_output['output'] = args.get('result', 'Completed without result.')
                break
            else:
                result = f'Unknown tool: {tool}'
            messages.append({'role': 'assistant', 'content': raw_content})
            messages.append({'role': 'user', 'content': f'TOOL OUTPUT: {result}'})
            step_counter += 1
    finally:
        browser.close()
    return final_output
