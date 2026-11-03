import logging
from typing import Optional
import groq

from ytrag.config import settings

logger = logging.getLogger("ytrag.groq")

_groq_client: Optional[groq.Groq] = None


def get_groq_client() -> groq.Groq:
    """Get or initialize singleton Groq client."""
    global _groq_client
    if _groq_client is None:
        settings.validate_for_answering()
        _groq_client = groq.Groq(api_key=settings.groq_api_key)
    return _groq_client


def generate_completion(
    system_prompt: str,
    user_prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.1,
    max_tokens: int = 800,
) -> str:
    """Call Groq LLM API with grounding-focused temperature and return text response."""
    client = get_groq_client()
    target_model = model or settings.llm_model

    logger.info(f"Generating completion with Groq model '{target_model}'...")
    response = client.chat.completions.create(
        model=target_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    answer_text = response.choices[0].message.content or ""
    return answer_text.strip()
