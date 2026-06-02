from prompts import CONVERSATIONAL_AGENT_PROMPT

def stream_conversational_agent(user_input: str, client, update_callback, system_memory: list) -> dict:
    """Streams conversational logic back via update_callback."""
    messages = []
    dict = {"role": "system", "content": CONVERSATIONAL_AGENT_PROMPT}
    messages.append(dict)
    for log in system_memory[-4:]:
        # 1. Correctly check if the dictionary has these specific keys
        if log.get("user_intent") and log.get("stdout"):
            # 2. Give the user's string to the user role
            messages.append({"role": "user", "content": log["user_intent"]})
            # 3. Give the actual AI output string to the assistant role
            messages.append({"role": "assistant", "content": log["stdout"]})
    
    messages.append({"role": "user", "content": user_input})
    response = client.chat.send(
        model="qwen/qwen3-32b",
        messages=messages,
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
