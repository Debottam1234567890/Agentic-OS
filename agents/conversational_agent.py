from prompts import CONVERSATIONAL_AGENT_PROMPT

def stream_conversational_agent(user_input: str, client, update_callback) -> dict:
    """Streams conversational logic back via update_callback."""
    response = client.chat.send(
        model="qwen/qwen3-32b",
        messages=[
            {"role": "system", "content": CONVERSATIONAL_AGENT_PROMPT},
            {"role": "user", "content": user_input}
        ],
        stream=True,
    )
    
    full_output = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            text_chunk = chunk.choices[0].delta.content
            full_output += text_chunk
            update_callback(text_chunk)
            
    return {
        "agent_title": "Conversational Agent",
        "agent_color": "#FF00FF",  # Magenta glow
        "command": "Conversational Query",
        "output": full_output
    }
