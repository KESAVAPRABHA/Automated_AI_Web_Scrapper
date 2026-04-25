#loads values from .env automatically
import os
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
# OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
DEFAULT_MAX_PAGES: int = 10
DEFAULT_RATE_LIMIT_DELAY: float = 1.0   # seconds between requests
DEFAULT_MODEL: str = "gemini-2.5-flash"

if not GOOGLE_API_KEY:
    import warnings
    warnings.warn(
        "GOOGLE_API_KEY is not set.",
        stacklevel=2,
    )
