import os
import base64
def analyze_image(file_path: str, client, user_query: str, code_context: str='') -> str:
    with open(file_path, 'rb') as f:
        base64_image = base64.b64encode(f.read()).decode('utf-8')
        final_query = user_query
        if code_context:
            final_query += f'\n\n[HYBRID CONTEXT] Here is the raw text of the most recently modified file in the workspace to help you check for subtle syntax errors that might be hard to see in the image:\n{code_context}'
        content_array = [{'type': 'text', 'text': final_query}, {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{base64_image}'}}]
        response = client.chat.send(model=os.environ.get('AGENTIC_OS_MODEL', 'openrouter:free'), messages=[{'role': 'user', 'content': content_array}], stream=False)
        return response.choices[0].message.content.strip()
