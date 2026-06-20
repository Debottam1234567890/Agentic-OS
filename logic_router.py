import traceback
import os
import re
import time
from prompts import ROUTER_PROMPT

# -- List of free models to try, in order, if the primary model fails or is rate-limited --
FALLBACK_MODELS = [
    'google/gemma-4-31b-it:free',
    'google/gemma-4-26b-a4b-it:free',
    'google/gemma-4-31b-it:free',
    'openai/gpt-oss-20b:free',
]

_DIAG_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'route_intent_diag.log')
def _diag(msg):
    with open(_DIAG_LOG, 'a') as f:
        f.write(msg + '\n')

def _strip_thinking(text: str) -> str:
    """Strip <think>...</think> tags that many free/reasoning models wrap around their answers."""
    if not text:
        return ''
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return cleaned.strip()

def route_intent(user_input: str, client) -> str:
    _diag('\n' + '=' * 80)
    _diag('[DIAG] route_intent CALLED')
    _diag(f'[DIAG] User input: {user_input!r}')
    _diag('=' * 80)

    # Determine which model(s) to try
    user_model = os.environ.get('AGENTIC_OS_MODEL', '').strip()
    models_to_try = ([user_model] if user_model else []) + FALLBACK_MODELS
    # Deduplicate while preserving order
    seen = set()
    unique_models = []
    for m in models_to_try:
        if m not in seen:
            seen.add(m)
            unique_models.append(m)

    valid = ['TERMINAL', 'CONVERSATIONAL', 'WEB']

    for model in unique_models:
        _diag(f'[DIAG] Trying model: {model}')
        try:
            response = client.chat.send(
                model=model,
                messages=[
                    {'role': 'system', 'content': ROUTER_PROMPT},
                    {'role': 'user', 'content': user_input}
                ],
                stream=False
            )
            raw_content = getattr(getattr(response.choices[0], 'message', None), 'content', None)
            _diag(f'[DIAG] Raw content from {model}: {raw_content!r}')

            # Strip <think> tags and clean up the response
            cleaned = _strip_thinking(raw_content or '')
            stripped = cleaned.strip().upper()
            _diag(f'[DIAG] After cleaning: {stripped!r}')

            # Check for valid category (substring match for robustness)
            matched = [v for v in valid if v in stripped]
            if matched:
                result = matched[0]
                _diag(f'[DIAG] SUCCESS: matched {result!r} using model {model}')
                return result
            else:
                _diag(f'[DIAG] No valid category found in response, trying next model...')
                continue

        except Exception as e:
            _diag(f'[DIAG] Model {model} failed: {type(e).__name__}: {e}')
            # If rate-limited, wait briefly then try next model
            if '429' in str(e) or 'TooManyRequests' in type(e).__name__:
                _diag('[DIAG] Rate limited, waiting 2s before trying next model...')
                time.sleep(2)
            continue

    # If all models failed, default to CONVERSATIONAL so the OS doesn't crash
    _diag('[DIAG] ALL models failed, defaulting to CONVERSATIONAL')
    _diag('=' * 80 + '\n')
    return 'CONVERSATIONAL'
