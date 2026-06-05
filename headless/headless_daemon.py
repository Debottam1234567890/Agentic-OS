import time
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
class HeadlessBrowser:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
    def start(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True, args=['--headless=new', '--disable-blink-features=AutomationControlled', '--no-sandbox'])
        context = self.browser.new_context(user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36', viewport={'width': 1280, 'height': 900}, locale='en-US', timezone_id='America/New_York', java_script_enabled=True)
        self.page = context.new_page()
        Stealth().apply_stealth_sync(self.page)
    def _wait_for_stable(self):
        try:
            self.page.wait_for_load_state('domcontentloaded', timeout=5000)
        except Exception:
            pass
        try:
            self.page.wait_for_load_state('networkidle', timeout=4000)
        except Exception:
            pass
        self._dismiss_popups()
    def _dismiss_popups(self):
        dismiss_selectors = ["button:has-text('Accept')", "button:has-text('Accept All')", "button:has-text('Got it')", "button:has-text('I agree')", "button:has-text('Close')", "button:has-text('Dismiss')", "[id*='cookie'] button", "[class*='cookie'] button", "[id*='consent'] button", "[class*='consent'] button"]
        for sel in dismiss_selectors:
            try:
                el = self.page.query_selector(sel)
                if el and el.is_visible():
                    el.click(force=True)
                    time.sleep(0.3)
                    break
            except Exception:
                continue
    def navigate(self, url: str) -> str:
        try:
            self.page.goto(url, timeout=15000, wait_until='domcontentloaded')
            self._wait_for_stable()
            return f'Navigated to {url}. Current URL: {self.page.url}'
        except Exception as e:
            return f'Failed to navigate: {e}'
    def click(self, node_id: str) -> str:
        try:
            selector = f"[agent-id='{node_id}']"
            self.page.click(selector, timeout=5000, force=True)
            self._wait_for_stable()
            return f'Clicked [{node_id}]. Current URL: {self.page.url}'
        except Exception as e:
            return f'Error clicking [{node_id}]: {e}'
    def type_text(self, node_id: str, text: str) -> str:
        try:
            selector = f"[agent-id='{node_id}']"
            self.page.fill(selector, text, timeout=5000, force=True)
            return f"Typed '{text}' into [{node_id}]."
        except Exception as e:
            return f'Error typing into [{node_id}]: {e}'
    def press_enter(self) -> str:
        try:
            self.page.keyboard.press('Enter')
            self._wait_for_stable()
            return f'Pressed Enter. Current URL: {self.page.url}'
        except Exception as e:
            return f'Error pressing Enter: {e}'
    def get_dom_snapshot(self) -> str:
        try:
            enumeration_js = '() => {\n    const SELECTORS = \'a, button, input, textarea, select, [role="button"], [role="link"], [role="tab"], [tabindex]:not([tabindex="-1"])\';\n    const els = document.querySelectorAll(SELECTORS);\n    const lines = [];\n    let id = 1;\n    for (const el of els) {\n        const rect = el.getBoundingClientRect();\n        if (rect.width <= 0 || rect.height <= 0) continue;\n        const style = window.getComputedStyle(el);\n        if (style.display === \'none\' || style.visibility === \'hidden\' || style.opacity === \'0\') continue;\n        el.setAttribute(\'agent-id\', String(id));\n        let label = (\n            el.innerText ||\n            el.value ||\n            el.placeholder ||\n            el.getAttribute(\'aria-label\') ||\n            el.getAttribute(\'title\') ||\n            el.name ||\n            \'\'\n        ).replace(/\\s+/g, \' \').trim().substring(0, 60);\n        const tag = el.tagName;\n        let extra = \'\';\n        if (tag === \'A\' && el.href) extra = \' href=\' + el.href.substring(0, 80);\n        if (tag === \'INPUT\') extra = \' type=\' + (el.type || \'text\');\n        if (label || extra) {\n            lines.push(\'[\' + id + \'] \' + tag + \': "\' + label + \'"\' + extra);\n        }\n        id++;\n    }\n    return lines.join(\'\\n\');\n}'
            interactables = self.page.evaluate(enumeration_js)
            body_text = self.page.inner_text('body', timeout=5000)
            clean_text = ' '.join(body_text.split())[:4000]
            url_line = f'CURRENT URL: {self.page.url}'
            title_line = f'PAGE TITLE: {self.page.title()}'
            return f'{url_line}\n{title_line}\n\n--- INTERACTIVE ELEMENTS ---\n{interactables}\n\n--- PAGE TEXT (first 4000 chars) ---\n{clean_text}'
        except Exception as e:
            return f'Error extracting DOM: {e}'
    def scroll(self, direction: str) -> str:
        try:
            if direction == 'down':
                self.page.evaluate('window.scrollBy(0, window.innerHeight * 0.8)')
            elif direction == 'up':
                self.page.evaluate('window.scrollBy(0, -window.innerHeight * 0.8)')
            else:
                return "Invalid direction. Use 'up' or 'down'."
            time.sleep(0.3)
            return f'Scrolled {direction}.'
        except Exception as e:
            return f'Error scrolling: {e}'
    def get_page_url(self) -> str:
        return f'Current URL: {self.page.url}'
    def close(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
