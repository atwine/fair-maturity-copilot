"""One OpenAI-compatible client. Ollama (dev) and vLLM (pilot) both speak
this API, so switching providers is exactly the three env vars in
config.py — never a code change. See .env.example."""

from openai import OpenAI

from app.config import settings


def get_client() -> OpenAI:
    return OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)


def generate(prompt: str, *, max_tokens: int = 300, temperature: float = 0.4) -> str:
    client = get_client()
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return (response.choices[0].message.content or "").strip()


def generate_chat(messages: list[dict], *, max_tokens: int = 400, temperature: float = 0.4) -> str:
    """Like generate(), but for a real multi-turn conversation (the mentor,
    Checkpoint 9) instead of one self-contained prompt -- messages is the
    full running history (system + prior turns + the newest user message),
    same OpenAI-compatible shape either provider (vLLM/Ollama) accepts."""
    client = get_client()
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return (response.choices[0].message.content or "").strip()
