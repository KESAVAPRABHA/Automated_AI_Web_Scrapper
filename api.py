#FastAPI backend for the AI Web Scraper.
#Command: uvicorn api:app --reload --port 8000
import sys
import logging
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

# Fix for Playwright/asyncio NotImplementedError on Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import io
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl

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
)


class CrawlRequest(BaseModel):
    url: str
    max_pages: int = 5
    use_js: bool = False


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
    filename: Optional[str] = "scraper_results"


def generate_filename(name: str) -> str:
    if not name:
        return "scraper_results"
    safe_name = name.strip().lower().replace(" ", "_")
    safe_name = safe_name.split("_")[0]
    
    return safe_name


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok", "version": "2.0.0"}


@app.post("/api/crawl", response_model=CrawlResponse)
async def crawl(req: CrawlRequest) -> CrawlResponse:
    #Crawl a website and return the scraped pages.
    try:
        if req.use_js:
            crawler = PlaywrightCrawler(delay=1.0)
        else:
            crawler = Crawler(delay=0.8)

        # Run blocking crawler in thread pool to not block event loop
        loop = asyncio.get_event_loop()
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
    #Run AI extraction on previously crawled pages.
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
    # Export extracted records as CSV / JSON / Excel.
    if not req.records:
        raise HTTPException(status_code=400, detail="No records to export.")
    
    try:
        exporter = Exporter()
        raw_bytes = exporter.to_bytes(req.records, req.fmt)

        mime_map = {
            "csv":   "text/csv",
            "json":  "application/json",
            "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }

        ext_map = {
            "csv": "csv",
            "json": "json",
            "excel": "xlsx"
        }

        fmt = req.fmt.lower()

        #Generate dynamic filename
        safe_name = generate_filename(req.filename)

        return StreamingResponse(
            io.BytesIO(raw_bytes),
            media_type=mime_map.get(fmt, "application/octet-stream"),
            headers={
                "Content-Disposition": f'attachment; filename="{safe_name}.{ext_map.get(fmt, fmt)}"'
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
