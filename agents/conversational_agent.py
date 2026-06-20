import os
from prompts import CONVERSATIONAL_AGENT_PROMPT
from agents.rag_agent import retrieve
def stream_conversational_agent(user_input: str, client, update_callback, system_memory: list) -> dict:
    messages = []
    if user_input.lower().startswith('query_vault:'):
        clean_query = user_input[12:].strip()
        update_callback('> *Searching Knowledge Vault...*\n\n')
        retrieved_data = retrieve(clean_query)
        messages.append({'role': 'system', 'content': CONVERSATIONAL_AGENT_PROMPT})
        messages.append({'role': 'user', 'content': f"Answer the user's question using ONLY this Context: {retrieved_data}\n\nQuestion: {clean_query}"})
    else:
        messages.append({'role': 'system', 'content': CONVERSATIONAL_AGENT_PROMPT})
        for log in system_memory[-4:]:
            if log.get('user_intent') and log.get('stdout'):
                messages.append({'role': 'user', 'content': log['user_intent']})
                messages.append({'role': 'assistant', 'content': log['stdout']})
        messages.append({'role': 'user', 'content': user_input})
    response = client.chat.send(model=os.environ.get('AGENTIC_OS_MODEL', 'qwen/qwen3-coder:free'), messages=messages, stream=True)
    full_output = ''
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            text_chunk = chunk.choices[0].delta.content
            full_output += text_chunk
            update_callback(text_chunk)
    return {'agent_title': 'Conversational Agent', 'agent_color': '#FF00FF', 'command': 'Conversational Query', 'output': full_output}
