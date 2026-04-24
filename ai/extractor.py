import json
import logging
import re
import socket
from typing import Any, Dict, List

from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ai.prompts import CHAT_PROMPT, EXTRACTION_PROMPT
from config import DEFAULT_MODEL, GOOGLE_API_KEY

logger = logging.getLogger(__name__)

# Maximum characters of page text sent to the LLM per call
_PAGE_TEXT_LIMIT = 12_000
# Maximum characters of combined pages text for chat queries (Gemini 2.5 Flash has 1M token ctx)
_CHAT_TEXT_LIMIT = 40_000


def _is_network_error(exc: Exception) -> bool:
    """Return True for transient network / DNS errors worth retrying."""
    msg = str(exc).lower()
    return any(k in msg for k in ("getaddrinfo", "connection", "timeout", "503", "429"))


class AIExtractor:

    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is not set.")
        self._llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=GOOGLE_API_KEY,
            temperature=0.1,
        )
        self._extraction_chain = EXTRACTION_PROMPT | self._llm | StrOutputParser()
        self._chat_chain = CHAT_PROMPT | self._llm | StrOutputParser()

    @staticmethod
    def _parse_json(raw: str) -> Dict[str, Any]:
        """Safely parse JSON from LLM output, stripping markdown fences."""
        raw = raw.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.warning("JSON parse failed (%s). Raw snippet: %s", exc, raw[:300])
            return {}

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _invoke_extraction(self, inputs: dict) -> str:
        return self._extraction_chain.invoke(inputs)

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _invoke_chat(self, inputs: dict) -> str:
        return self._chat_chain.invoke(inputs)

    def extract(
        self,
        page_text: str,
        fields: List[str],
        url: str = "",
    ) -> Dict[str, Any]:
        try:
            raw = self._invoke_extraction(
                {
                    "fields": ", ".join(fields),
                    "page_text": page_text[:_PAGE_TEXT_LIMIT],
                    "url": url,
                }
            )
            result = self._parse_json(raw)
            if not result:
                return {f: None for f in fields}
            return result
        except Exception as exc:
            logger.error("extract() error: %s", exc)
            if _is_network_error(exc):
                raise ConnectionError(
                    f"Network error reaching Gemini API — check your internet connection. Detail: {exc}"
                ) from exc
            return {f: None for f in fields}

    def chat_extract(
        self,
        user_query: str,
        pages: List[Dict],
        url: str,
    ) -> Dict[str, Any]:
        # Build combined pages summary with a per-page cap so all pages contribute
        segments = []
        per_page_cap = max(2000, _CHAT_TEXT_LIMIT // max(len(pages), 1))
        budget = _CHAT_TEXT_LIMIT
        for page in pages:
            txt = page.get("text", "").strip()
            segment = f"[Page: {page['url']}]\n{txt[:per_page_cap]}"
            if budget <= 0:
                break
            segments.append(segment[:budget])
            budget -= len(segment)

        pages_summary = "\n\n---\n\n".join(segments)

        try:
            raw = self._invoke_chat(
                {
                    "user_query": user_query,
                    "pages_summary": pages_summary,
                    "url": url,
                }
            )
            parsed = self._parse_json(raw)
            if not parsed:
                return {"answer": raw, "data": []}
            parsed.setdefault("answer", "")
            parsed.setdefault("data", [])
            return parsed
        except Exception as exc:
            logger.error("chat_extract() error: %s", exc)
            if _is_network_error(exc):
                err_msg = (
                    "Network error: Could not reach the Gemini API. "
                    "Please check your internet connection and try again."
                )
            else:
                err_msg = f"AI error: {exc}"
            return {"answer": err_msg, "data": []}
