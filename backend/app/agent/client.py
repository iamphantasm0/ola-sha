from openai import AsyncOpenAI

from app.core.config import settings

# 0G Compute Router is OpenAI-compatible — only the base_url differs.
og_client = AsyncOpenAI(
    base_url=settings.OG_COMPUTE_BASE_URL,
    api_key=settings.OG_COMPUTE_API_KEY,
)
