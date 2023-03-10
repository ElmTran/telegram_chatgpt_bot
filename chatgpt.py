import openai
from config import Config


def ask(messages):
    resp = openai.ChatCompletion.create(
        model=Config.openai.model,
        messages=messages,
        api_key=Config.openai.api_key,
    )
    ans = resp["choices"][0]["message"]["content"]
    return ans
