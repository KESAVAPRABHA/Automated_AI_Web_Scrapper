"""Central configuration — loads values from .env automatically."""
import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ───────────────────────────────────────────────────────────────────
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
# OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# ── Crawl Defaults ─────────────────────────────────────────────────────────────
DEFAULT_MAX_PAGES: int = 10
DEFAULT_RATE_LIMIT_DELAY: float = 1.0   # seconds between requests
DEFAULT_MODEL: str = "gemini-2.5-flash"

# ── Validation ─────────────────────────────────────────────────────────────────
if not GOOGLE_API_KEY:
    import warnings
    warnings.warn(
        "GOOGLE_API_KEY is not set. Copy .env.example → .env and add your key.",
        stacklevel=2,
    )
