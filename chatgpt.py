import openai
from config import cfg


def ask(messages):
    resp = openai.ChatCompletion.create(
        model=cfg.get('openai', 'model'),
        messages=messages,
        api_key=cfg.get('openai', 'api_key'),
    )
    ans = resp["choices"][0]["message"]["content"]
    return ans
