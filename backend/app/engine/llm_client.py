"""One OpenAI-compatible client. Ollama, vLLM, and OpenRouter all speak
this API, so switching providers is exactly the three env vars in
config.py — never a code change. See .env.example.

max_tokens defaults are set generously (1200+), not tightly, on purpose:
a reasoning model (DeepSeek-R1-style, o1-style -- something OpenRouter's
"auto" router can pick per request without warning) spends completion
tokens on invisible "thinking" before it writes anything visible. A
budget sized for a plain model's actual answer (was 300/400) can be
entirely consumed by that hidden reasoning, so the call finishes with
finish_reason "length" and an EMPTY visible reply -- not an error, not a
timeout, just silence. Reproduced live: openrouter/auto routed to
deepseek/deepseek-v4-flash-0731, which used all 400 allotted tokens on
reasoning_tokens alone on 2 of 3 test turns. Raising the cap doesn't cost
anything against a plain model (max_tokens is a ceiling, not a target --
vLLM's Llama still stops on its own once it's actually done), it only
matters the moment a reasoning model gets picked underneath us.

Even 1200 isn't a safe fixed number, though: reproduced live again on a
remediation prompt where deepseek/deepseek-v4-flash-0731 spent 900-1200+
reasoning tokens BY ITSELF on 2 of 3 attempts, leaving nothing for the
visible answer at a 1200 cap. There's no fixed budget that's provably
enough against an auto-router that can hand the request to a different
reasoning model at any time -- so instead of guessing a bigger magic
number, both functions below retry once with a much larger budget
whenever a response comes back empty with finish_reason "length". Costs
nothing on the (overwhelmingly common) case where the first attempt
already produced real content."""

from openai import OpenAI

from app.config import settings

_RETRY_MAX_TOKENS = 4000


def get_client() -> OpenAI:
    return OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)


def generate(prompt: str, *, max_tokens: int = 1200, temperature: float = 0.4) -> str:
    client = get_client()
    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    choice = response.choices[0]
    text = (choice.message.content or "").strip()
    if not text and choice.finish_reason == "length" and max_tokens < _RETRY_MAX_TOKENS:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            max_tokens=_RETRY_MAX_TOKENS,
            temperature=temperature,
        )
        text = (response.choices[0].message.content or "").strip()
    return text


def generate_chat(messages: list[dict], *, max_tokens: int = 1200, temperature: float = 0.4) -> str:
    """Like generate(), but for a real multi-turn conversation (the mentor,
    Checkpoint 9) instead of one self-contained prompt -- messages is the
    full running history (system + prior turns + the newest user message),
    same OpenAI-compatible shape every provider here accepts."""
    client = get_client()
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    choice = response.choices[0]
    text = (choice.message.content or "").strip()
    if not text and choice.finish_reason == "length" and max_tokens < _RETRY_MAX_TOKENS:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            max_tokens=_RETRY_MAX_TOKENS,
            temperature=temperature,
        )
        text = (response.choices[0].message.content or "").strip()
    return text
