# FastAPI backend for the AI Web Scraper.
# Command: uvicorn api:app --reload --port 8000

import sys
import logging
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup
from utils.helpers import make_absolute, normalize_url
# Fix for Playwright/asyncio NotImplementedError on Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import io
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent))

from scraper.crawler import Crawler
from scraper.playwright_crawler import PlaywrightCrawler
from ai.extractor import AIExtractor
from export.exporter import Exporter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Web Scraper API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

class CrawlRequest(BaseModel):
    url: str
    max_pages: int = 5
    use_js: bool = False
    fields: Optional[List[str]] = None


class CrawlResponse(BaseModel):
    pages: List[Dict[str, Any]]
    count: int


class ChatRequest(BaseModel):
    user_query: str
    pages: List[Dict[str, Any]]
    url: str


class ChatResponse(BaseModel):
    answer: str
    data: List[Dict[str, Any]]


class ExportRequest(BaseModel):
    records: List[Dict[str, Any]]
    fmt: str = "csv"
    filename: Optional[str] = None          # optional manual filename
    user_query: Optional[str] = None        # fallback (AUTO)


def generate_filename(name: str) -> str:
    if not name:
        return "scraper_results"
    stop_words = {"give", "me", "the", "list", "show", "get", "all","for","from","you","download"}
    words = name.lower().strip().split()
    words = [w for w in words if w not in stop_words]
    safe_name = "_".join(words)
    safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")

    return safe_name or "scraper_results"


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok", "version": "2.0.0"}


@app.post("/api/crawl", response_model=CrawlResponse)
async def crawl(req: CrawlRequest) -> CrawlResponse:
    try:
        if req.use_js:
            crawler = PlaywrightCrawler(delay=1.0)
        else:
            crawler = Crawler(delay=0.8)

        loop = asyncio.get_event_loop()

        if req.fields:
            logger.info("Performing SMART CRAWL for fields: %s", req.fields)
            # Just crawl the homepage to get links
            initial_pages = await loop.run_in_executor(
                None,
                lambda: crawler.crawl(start_url=req.url.strip(), max_pages=1)
            )
            if not initial_pages:
                return CrawlResponse(pages=[], count=0)
            
            #Extract links from homepage
            soup = BeautifulSoup(initial_pages[0]['html'], "lxml")
            raw_links = []
            for a in soup.find_all("a", href=True):
                abs_url = make_absolute(req.url.strip(), a['href'])
                raw_links.append(normalize_url(abs_url))
            
            # AI to pick the best links
            extractor = AIExtractor()
            target_urls = await loop.run_in_executor(
                None,
                lambda: extractor.select_relevant_links(req.fields, raw_links, req.url.strip())
            )
            
            # Crawl ONLY the target URLs (plus the homepage we already have)
            final_pages = [initial_pages[0]]
            # Use a set to avoid recrawling the homepage if the AI picked it
            to_crawl = [u for u in target_urls if u != initial_pages[0]['url']]
            
            for url in to_crawl[:req.max_pages - 1]:
                page_data = await loop.run_in_executor(
                    None,
                    lambda u=url: crawler.crawl(start_url=u, max_pages=1)
                )
                if page_data:
                    final_pages.append(page_data[0])
            
            return CrawlResponse(pages=final_pages, count=len(final_pages))

        # Default BFS Crawl
        pages = await loop.run_in_executor(
            None,
            lambda: crawler.crawl(
                start_url=req.url.strip(),
                max_pages=int(req.max_pages),
                same_domain=True,
            ),
        )
        return CrawlResponse(pages=pages, count=len(pages))

    except Exception as exc:
        logger.error("Crawl error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    try:
        extractor = AIExtractor()
        loop = asyncio.get_event_loop()

        result = await loop.run_in_executor(
            None,
            lambda: extractor.chat_extract(
                user_query=req.user_query,
                pages=req.pages,
                url=req.url,
            ),
        )

        return ChatResponse(
            answer=result.get("answer", ""),
            data=result.get("data", []),
        )

    except Exception as exc:
        logger.error("Chat error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/export")
async def export_data(req: ExportRequest):

    if not req.records:
        raise HTTPException(status_code=400, detail="No records to export.")

    try:
        exporter = Exporter()
        raw_bytes = exporter.to_bytes(req.records, req.fmt)

        mime_map = {
            "csv": "text/csv",
            "json": "application/json",
            "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }

        ext_map = {
            "csv": "csv",
            "json": "json",
            "excel": "xlsx",
        }

        fmt = req.fmt.lower()
        name_source = req.filename or req.user_query or "scraper_results"
        safe_name = generate_filename(name_source)

        return StreamingResponse(
            io.BytesIO(raw_bytes),
            media_type=mime_map.get(fmt, "application/octet-stream"),
            headers={
                "Content-Disposition": f'attachment; filename="{safe_name}.{ext_map.get(fmt, fmt)}"'
            },
        )

    except Exception as exc:
        logger.error("Export error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))