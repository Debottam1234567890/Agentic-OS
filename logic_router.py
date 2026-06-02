from prompts import ROUTER_PROMPT

def route_intent(user_input: str, client) -> str:
    """Classifies user intent into TERMINAL, CONVERSATIONAL, or WEB."""
    try:
        response = client.chat.send(
            model="qwen/qwen3-32b",
            messages=[
                {"role": "system", "content": ROUTER_PROMPT},
                {"role": "user", "content": user_input}
            ],
            stream=False,
        )
        return response.choices[0].message.content.strip().upper()
    except Exception as e:
        return "ERROR"
