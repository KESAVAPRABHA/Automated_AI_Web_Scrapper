"""
Automated AI Web Scraper — Streamlit Chat UI
Run with: streamlit run app.py
"""
import sys
import logging
import asyncio
from pathlib import Path

# Fix for Playwright/asyncio NotImplementedError on Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from scraper.crawler import Crawler
from scraper.playwright_crawler import PlaywrightCrawler
from ai.extractor import AIExtractor
from export.exporter import Exporter

logging.basicConfig(level=logging.INFO)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Web Scraper",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Root / Body ── */
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', sans-serif;
    background: #0d0f1a;
    color: #e2e8f0;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111827 0%, #0d1117 100%);
    border-right: 1px solid rgba(99,102,241,0.2);
}

/* ── Header banner ── */
.hero-header {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #06b6d4 100%);
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 24px;
    box-shadow: 0 8px 32px rgba(99,102,241,0.35);
    position: relative;
    overflow: hidden;
}
.hero-header::before {
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 180px; height: 180px;
    background: rgba(255,255,255,0.06);
    border-radius: 50%;
}
.hero-header h1 {
    margin: 0; font-size: 1.75rem; font-weight: 700;
    color: #fff; letter-spacing: -0.5px;
}
.hero-header p {
    margin: 6px 0 0; font-size: 0.9rem; color: rgba(255,255,255,0.8);
}

/* ── Status badges ── */
.status-badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 12px; border-radius: 20px; font-size: 0.78rem;
    font-weight: 600; margin-bottom: 12px;
}
.status-badge.ready   { background: rgba(16,185,129,0.15); color: #10b981; border: 1px solid rgba(16,185,129,0.3); }
.status-badge.loading { background: rgba(245,158,11,0.15);  color: #f59e0b; border: 1px solid rgba(245,158,11,0.3); }
.status-badge.idle    { background: rgba(100,116,139,0.15); color: #94a3b8; border: 1px solid rgba(100,116,139,0.2); }

/* ── Chat messages ── */
.chat-wrapper {
    display: flex; flex-direction: column; gap: 16px;
    padding: 8px 0 100px;
}

.chat-bubble {
    display: flex; gap: 12px; align-items: flex-start;
    animation: fadeInUp 0.3s ease;
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}

.chat-avatar {
    width: 36px; height: 36px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; flex-shrink: 0; margin-top: 2px;
}
.avatar-ai   { background: linear-gradient(135deg,#6366f1,#8b5cf6); }
.avatar-user { background: linear-gradient(135deg,#0ea5e9,#06b6d4); }

.chat-content {
    background: #1e2433;
    border: 1px solid rgba(99,102,241,0.15);
    border-radius: 0 16px 16px 16px;
    padding: 14px 18px; max-width: 80%;
    line-height: 1.65; font-size: 0.92rem; color: #e2e8f0;
}
.chat-content.user-msg {
    background: linear-gradient(135deg,rgba(14,165,233,0.12),rgba(6,182,212,0.08));
    border-color: rgba(14,165,233,0.25);
    border-radius: 16px 0 16px 16px;
    margin-left: auto;
}

/* ── Data table inside chat ── */
.data-table-wrap {
    margin-top: 14px;
    border-radius: 10px; overflow: hidden;
    border: 1px solid rgba(99,102,241,0.25);
}
.data-table-wrap table {
    width:100%; border-collapse: collapse; font-size: 0.83rem;
}
.data-table-wrap th {
    background: rgba(99,102,241,0.25);
    color: #c4b5fd; padding: 8px 12px; text-align: left;
    font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;
    font-size: 0.72rem;
}
.data-table-wrap td {
    padding: 8px 12px; border-top: 1px solid rgba(99,102,241,0.1);
    color: #e2e8f0;
}
.data-table-wrap tr:hover td { background: rgba(99,102,241,0.06); }

/* ── Sidebar inputs ── */
.sidebar-section-title {
    font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.1em; color: #6366f1; margin: 20px 0 8px;
}
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] select {
    background: #1e2433 !important;
    border: 1px solid rgba(99,102,241,0.3) !important;
    border-radius: 8px !important; color: #e2e8f0 !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 2px rgba(99,102,241,0.2) !important;
}

/* ── Buttons ── */
[data-testid="stButton"] > button {
    background: linear-gradient(135deg,#6366f1,#8b5cf6) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
}
[data-testid="stButton"] > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(99,102,241,0.5) !important;
}

/* ── Download button ── */
[data-testid="stDownloadButton"] > button {
    background: rgba(16,185,129,0.15) !important;
    color: #10b981 !important;
    border: 1px solid rgba(16,185,129,0.4) !important;
    border-radius: 10px !important; font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    width: 100% !important;
    transition: all 0.2s ease !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background: rgba(16,185,129,0.25) !important;
}

/* ── Chat input bar ── */
[data-testid="stChatInput"] {
    background: #1e2433 !important;
    border: 1px solid rgba(99,102,241,0.3) !important;
    border-radius: 14px !important;
}

/* ── Metrics ── */
[data-testid="metric-container"] {
    background: #1e2433;
    border: 1px solid rgba(99,102,241,0.15);
    border-radius: 10px; padding: 12px 16px;
}

/* ── Separator ── */
hr { border-color: rgba(99,102,241,0.15) !important; }

/* ── Spinner ── */
[data-testid="stSpinner"] { color: #6366f1 !important; }
</style>
""",
    unsafe_allow_html=True,
)

# ── Session state defaults ──────────────────────────────────────────────────────
def _init_state() -> None:
    defaults = {
        "messages": [],          # [{role, content, data}]
        "crawled_pages": [],     # [{url, text, html}]
        "current_url": "",
        "site_loaded": False,
        "last_records": [],      # last extracted structured records
        "crawling": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _records_to_html_table(records: list) -> str:
    """Convert a list of dicts to a styled HTML table string."""
    if not records:
        return ""
    df = pd.json_normalize(records)
    rows = ""
    headers = "".join(f"<th>{c}</th>" for c in df.columns)
    for _, row in df.iterrows():
        cells = "".join(f"<td>{row[c]}</td>" for c in df.columns)
        rows += f"<tr>{cells}</tr>"
    return (
        f'<div class="data-table-wrap"><table>'
        f"<thead><tr>{headers}</tr></thead>"
        f"<tbody>{rows}</tbody>"
        f"</table></div>"
    )


def _add_message(role: str, content: str, data: list | None = None) -> None:
    st.session_state.messages.append(
        {"role": role, "content": content, "data": data or []}
    )


def _render_messages() -> None:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="chat-bubble" style="flex-direction:row-reverse">'
                f'  <div class="chat-avatar avatar-user">👤</div>'
                f'  <div class="chat-content user-msg">{msg["content"]}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )
        else:
            table_html = _records_to_html_table(msg.get("data", []))
            st.markdown(
                f'<div class="chat-bubble">'
                f'  <div class="chat-avatar avatar-ai">🤖</div>'
                f'  <div class="chat-content">{msg["content"]}{table_html}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<p style="font-size:1.3rem;font-weight:700;margin:0">🕸️ AI Web Scraper</p>'
        '<p style="color:#94a3b8;font-size:0.8rem;margin:4px 0 20px">Powered by Gemini 2.5 Flash</p>',
        unsafe_allow_html=True,
    )

    st.markdown('<p class="sidebar-section-title">🌐 Target Website</p>', unsafe_allow_html=True)
    url_input = st.text_input(
        "Website URL",
        placeholder="https://example.com",
        label_visibility="collapsed",
        key="url_input_widget",
    )

    col_pages, col_js = st.columns(2)
    with col_pages:
        max_pages = st.number_input("Max Pages", min_value=1, max_value=50, value=5)
    with col_js:
        use_js = st.checkbox("Use JS", value=False, help="Playwright for JS-heavy sites")

    if st.button("🚀 Load Site", use_container_width=True):
        if not url_input.strip():
            st.error("Please enter a URL first.")
        else:
            with st.spinner("Crawling website…"):
                try:
                    if use_js:
                        crawler = PlaywrightCrawler(delay=1.0)
                    else:
                        crawler = Crawler(delay=0.8)

                    pages = crawler.crawl(
                        start_url=url_input.strip(),
                        max_pages=int(max_pages),
                        same_domain=True,
                    )
                    st.session_state.crawled_pages = pages
                    st.session_state.current_url = url_input.strip()
                    st.session_state.site_loaded = True
                    st.session_state.messages = []
                    st.session_state.last_records = []

                    _add_message(
                        "assistant",
                        f"✅ <b>Site loaded!</b> I crawled <b>{len(pages)}</b> page(s) from "
                        f"<code>{url_input.strip()}</code>.<br><br>"
                        "Now ask me anything — for example:<br>"
                        "• <i>\"Give me the leadership team names\"</i><br>"
                        "• <i>\"What products do they sell and at what price?\"</i><br>"
                        "• <i>\"Are there any frontend engineering openings?\"</i>",
                    )
                    st.rerun()
                except Exception as exc:
                    st.error(f"Crawl failed: {exc}")

    st.markdown("---")

    # Site status
    if st.session_state.site_loaded:
        st.markdown(
            '<span class="status-badge ready">● Site Ready</span>', unsafe_allow_html=True
        )
        st.caption(f"📄 {len(st.session_state.crawled_pages)} pages cached")
        st.caption(f"🔗 {st.session_state.current_url[:40]}{'…' if len(st.session_state.current_url)>40 else ''}")
    else:
        st.markdown(
            '<span class="status-badge idle">○ No site loaded</span>', unsafe_allow_html=True
        )

    # Export section
    if st.session_state.last_records:
        st.markdown('<p class="sidebar-section-title">📥 Export Last Results</p>', unsafe_allow_html=True)
        export_fmt = st.selectbox("Format", ["csv", "json", "excel"], key="export_fmt")

        exporter = Exporter()
        mime_map = {"csv": "text/csv", "json": "application/json", "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
        ext_map  = {"csv": "csv", "json": "json", "excel": "xlsx"}
        raw_bytes = exporter.to_bytes(st.session_state.last_records, export_fmt)

        st.download_button(
            label=f"⬇ Download .{ext_map[export_fmt]}",
            data=raw_bytes,
            file_name=f"scraper_results.{ext_map[export_fmt]}",
            mime=mime_map[export_fmt],
            use_container_width=True,
        )

    st.markdown("---")
    st.markdown(
        '<p style="font-size:0.72rem;color:#475569;text-align:center">'
        'Built with LangChain · Gemini · Streamlit</p>',
        unsafe_allow_html=True,
    )


# ── Main chat area ─────────────────────────────────────────────────────────────
st.markdown(
    '<div class="hero-header">'
    "  <h1>🕸️ AI Web Scraper</h1>"
    "  <p>Enter a website URL in the sidebar → Load Site → then ask me what to extract.</p>"
    "</div>",
    unsafe_allow_html=True,
)

# Stats row
if st.session_state.site_loaded:
    m1, m2, m3 = st.columns(3)
    m1.metric("Pages Crawled", len(st.session_state.crawled_pages))
    m2.metric("Messages", len(st.session_state.messages))
    m3.metric("Records Extracted", len(st.session_state.last_records))
    st.markdown("")

# Message history
if st.session_state.messages:
    st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)
    _render_messages()
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown(
        """
        <div style="text-align:center;padding:60px 20px;color:#475569">
            <div style="font-size:3.5rem;margin-bottom:16px">🕸️</div>
            <h3 style="color:#64748b;font-weight:600">Load a website to get started</h3>
            <p style="font-size:0.9rem">Enter a URL in the sidebar and click <b>Load Site</b><br>
            then chat with the AI to extract any data you need.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Chat input ─────────────────────────────────────────────────────────────────
placeholder = (
    "Ask me to extract data… e.g. 'Give me all leadership names and titles'"
    if st.session_state.site_loaded
    else "Load a website first using the sidebar →"
)

user_input = st.chat_input(placeholder, disabled=not st.session_state.site_loaded)

if user_input and user_input.strip():
    _add_message("user", user_input.strip())

    with st.spinner("🤖 Thinking…"):
        try:
            extractor = AIExtractor()
            result = extractor.chat_extract(
                user_query=user_input.strip(),
                pages=st.session_state.crawled_pages,
                url=st.session_state.current_url,
            )

            answer: str = result.get("answer", "")
            data: list  = result.get("data", [])

            # Update last_records if new data was returned
            if data:
                st.session_state.last_records = data

            _add_message("assistant", answer or "Here's what I found:", data=data)

        except Exception as exc:
            _add_message(
                "assistant",
                f"⚠️ <b>Error:</b> {exc}<br><br>"
                "Make sure your <code>GOOGLE_API_KEY</code> is set in the <code>.env</code> file.",
            )

    st.rerun()
