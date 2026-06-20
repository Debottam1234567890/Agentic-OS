import os
import requests
from bs4 import BeautifulSoup
from prompts import WEB_EXTRACTOR_PROMPT, WEB_SYNTHESIZER_PROMPT
def scrape_web(query: str) -> str:
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    url = f'https://html.duckduckgo.com/html/?q={query}'
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        snippets = soup.find_all('a', class_='result__snippet')
        top_3 = [s.get_text().strip() for s in snippets[:3]]
        return '\n'.join(top_3) if top_3 else 'No search results found. The site may have blocked the request.'
    except Exception as e:
        return f'Error during search: {e}'
def stream_web_agent(user_input: str, client, set_output, append_output) -> dict:
    query_response = client.chat.send(model=os.environ.get('AGENTIC_OS_MODEL', 'openrouter:free'), messages=[{'role': 'system', 'content': WEB_EXTRACTOR_PROMPT}, {'role': 'user', 'content': user_input}])
    search_query = query_response.choices[0].message.content.strip()
    live_data = scrape_web(search_query)
    if 'No search results found' in live_data:
        err_msg = f'**[X-Ray Scraper Data]:**\n> {live_data}\n\n---\n\n**[Agent Synthesis]:**\n⚠️ Scraper Error: The search engine blocked the request (Rate Limited).'
        set_output(err_msg)
        return {'agent_title': 'Web Agent', 'agent_color': '#FFFF00', 'command': f'Web Search: {search_query}', 'output': err_msg}
    base_msg = f'**[X-Ray Scraper Data]:**\n> {live_data}\n\n---\n\n**[Agent Synthesis]:**\n'
    set_output(base_msg)
    response = client.chat.send(model=os.environ.get('AGENTIC_OS_MODEL', 'openrouter:free'), messages=[{'role': 'system', 'content': WEB_SYNTHESIZER_PROMPT}, {'role': 'user', 'content': f"User Intent: {user_input}\n\nLive Web Data: {live_data}\n\nAnswer the user's intent using ONLY the live web data provided."}], stream=True)
    full_output = base_msg
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            text_chunk = chunk.choices[0].delta.content
            full_output += text_chunk
            append_output(text_chunk)
    return {'agent_title': 'Web Agent', 'agent_color': '#FFFF00', 'command': f'Web Search: {search_query}', 'output': full_output}
