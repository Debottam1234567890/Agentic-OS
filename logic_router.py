import traceback
import os
from prompts import ROUTER_PROMPT
_DIAG_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'route_intent_diag.log')
def _diag(msg):
    with open(_DIAG_LOG, 'a') as f:
        f.write(msg + '\n')
def route_intent(user_input: str, client) -> str:
    _diag('\n' + '=' * 80)
    _diag('[DIAG] route_intent CALLED')
    _diag(f'[DIAG] User input: {user_input!r}')
    _diag('=' * 80)
    try:
        response = client.chat.send(model='qwen/qwen3-32b', messages=[{'role': 'system', 'content': ROUTER_PROMPT}, {'role': 'user', 'content': user_input}], stream=False)
        _diag(f'[DIAG] Raw response type: {type(response)}')
        _diag(f'[DIAG] Raw response repr: {response!r}')
        choices = getattr(response, 'choices', None)
        _diag(f'[DIAG] response.choices type: {type(choices)}, value: {choices!r}')
        if choices is None or len(choices) == 0:
            _diag('[DIAG] ERROR: response.choices is None or empty!')
            return 'ERROR_NO_CHOICES'
        first_choice = choices[0]
        _diag(f'[DIAG] choices[0] type: {type(first_choice)}, repr: {first_choice!r}')
        message = getattr(first_choice, 'message', None)
        _diag(f'[DIAG] choices[0].message type: {type(message)}, repr: {message!r}')
        if message is None:
            _diag('[DIAG] ERROR: choices[0].message is None!')
            return 'ERROR_NO_MESSAGE'
        raw_content = getattr(message, 'content', None)
        _diag(f'[DIAG] RAW content type: {type(raw_content)}')
        _diag(f'[DIAG] RAW content repr: {raw_content!r}')
        _diag(f"[DIAG] RAW content length: {(len(raw_content) if raw_content else 'N/A')}")
        if raw_content is not None:
            _diag(f"[DIAG] Char-by-char ordinals: {[f'{c!r}(U+{ord(c):04X})' for c in raw_content]}")
        stripped = raw_content.strip().upper() if raw_content else ''
        _diag(f'[DIAG] After .strip().upper(): {stripped!r}')
        valid = ['TERMINAL', 'CONVERSATIONAL', 'WEB']
        matched = [v for v in valid if v in stripped]
        _diag(f'[DIAG] Matched categories (substring check): {matched}')
        _diag(f'[DIAG] Exact match in valid list: {stripped in valid}')
        _diag('=' * 80 + '\n')
        return stripped
    except Exception as e:
        _diag('\n' + '!' * 80)
        _diag(f'[DIAG] EXCEPTION in route_intent!')
        _diag(f'[DIAG] Exception type: {type(e).__name__}')
        _diag(f'[DIAG] Exception repr: {e!r}')
        _diag(f'[DIAG] Exception str:  {e}')
        _diag(f'[DIAG] Full traceback:')
        import io
        tb_buffer = io.StringIO()
        traceback.print_exc(file=tb_buffer)
        _diag(tb_buffer.getvalue())
        _diag('!' * 80 + '\n')
        return 'ERROR'
