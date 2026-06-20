import os
import requests
import re
from bs4 import BeautifulSoup
from rich.text import Text
from rich.markup import escape as rich_escape
def sanitize_rich_markup(text: str) -> str:
    try:
        Text.from_markup(text)
        return text
    except Exception:
        return rich_escape(text)
def fetch_and_clean_html(url: str, client) -> str:
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        garbage = ['script', 'style', 'nav', 'footer', 'header', 'aside', 'svg']
        for element in soup.find_all(garbage):
            element.extract()
        for a in soup.find_all('a', href=True):
            link_text = a.get_text(strip=True)
            if link_text:
                target_url = a['href']
                a.replace_with(f'{link_text} (URL: {target_url})')
        final_md = soup.get_text(separator='\n\n', strip=True)
        clean_input = final_md.replace('[', '(').replace(']', ')')
        SYSTEM_PROMPT = "You are a terminal UI renderer. Read the following raw scraped text and restructure it into a highly readable, clean document optimized for a CLI. CRITICAL: You must aggressively use Rich markup tags (e.g., [bold cyan], [dim], [#FF00FF], [italic yellow]) to color-code headers, highlight key terms, and distinguish interactive elements. Remove all useless boilerplate, cookie notices, and navigation noise. IMPORTANT RULE: NEVER use literal '[' or ']' brackets for anything OTHER than Rich markup tags. For citations, use parentheses like (1) instead of [1]. For links, just write 'Link Text (URL)' instead of Markdown brackets. Output ONLY the formatted text with Rich tags."
        try:
            response = client.chat.send(model=os.environ.get('AGENTIC_OS_MODEL', 'qwen/qwen3-coder:free'), messages=[{'role': 'system', 'content': SYSTEM_PROMPT}, {'role': 'user', 'content': f'Render this HTML content: {clean_input}'}], stream=False)
            structured_ui = response.choices[0].message.content.strip()
            structured_ui = re.sub('<think>.*?</think>', '', structured_ui, flags=re.DOTALL).strip()
            return sanitize_rich_markup(structured_ui)
        except Exception as e:
            return f'AI Structuring Failed. Falling back to raw text:\n\n{rich_escape(final_md)}'
    except Exception as e:
        return f'Error loading page: {str(e)}'
if __name__ == '__main__':
    print(fetch_and_clean_html('https://news.ycombinator.com', None))
