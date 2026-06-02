from prompts import CONVERSATIONAL_AGENT_PROMPT
from agents.rag_agent import retrieve 

def stream_conversational_agent(user_input: str, client, update_callback, system_memory: list) -> dict:
    """Streams conversational logic back via update_callback."""
    messages = []
    
    # ROUTE A: THE KNOWLEDGE VAULT
    if user_input.lower().startswith("query_vault:"):
        # FIX: Strings are immutable. You must assign the sliced string to a new variable.
        clean_query = user_input[12:].strip() 
        
        update_callback("> *Searching Knowledge Vault...*\n\n")
        retrieved_data = retrieve(clean_query)
        
        messages.append({"role": "system", "content": CONVERSATIONAL_AGENT_PROMPT})
        messages.append({
            "role": "user", 
            "content": f"Answer the user's question using ONLY this Context: {retrieved_data}\n\nQuestion: {clean_query}"
        })

    # ROUTE B: NORMAL CONVERSATIONAL MEMORY (FIX: Added ELSE block)
    else:
        messages.append({"role": "system", "content": CONVERSATIONAL_AGENT_PROMPT})
        for log in system_memory[-4:]:
            if log.get("user_intent") and log.get("stdout"):
                messages.append({"role": "user", "content": log["user_intent"]})
                messages.append({"role": "assistant", "content": log["stdout"]})
        
        messages.append({"role": "user", "content": user_input})
    
    # Send the safely routed messages array to the AI
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
        "agent_color": "#FF00FF",  
        "command": "Conversational Query",
        "output": full_output
    }