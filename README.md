# 🕸️ Automated AI Web Scraper

An AI-powered web scraper that accepts a website URL, crawls pages, extracts structured data using **Gemini 1.5 Flash** (via LangChain), and exports results as CSV / Excel / JSON.

Comes with a **React chatbot UI** where you can have a natural-language conversation about any website.

---

## ✨ Features

| Feature | Details |
|---|---|
| **Chatbot UI** | React chat interface |
| **Smart Crawling** | requests + BeautifulSoup (static) or Playwright (JS/SPA) |
| **AI Extraction** | LangChain + Gemini 1.5 Flash |
| **Any fields** | Ask for leadership names, prices, job openings — anything |
| **Export** | Download CSV, Excel (.xlsx), or JSON from the sidebar |
| **CLI** | Headless `python main.py` mode for scripting/automation |

---

## 🚀 Quick Start

### 1. Clone & install dependencies

```bash
pip install -r requirements.txt
playwright install chromium   # only needed for --js / JS sites
```

### 2. Set your API key

```bash
copy .env.example .env
# Edit .env and add your GOOGLE_API_KEY
# Get a free key at: https://aistudio.google.com/app/apikey
```

### 3. Launch the chatbot UI

```bash
streamlit run app.py
```

Then in the browser:
1. Paste a URL in the sidebar (e.g. `https://stripe.com/about`)
2. Click **🚀 Load Site**
3. Ask: *"Give me the leadership team names and titles"*
4. Download the result with the **Export** button

---

## 💻 CLI Usage

```bash
# Extract leadership names from a company page
python main.py --url https://stripe.com/about --fields "name" "title" --pages 2

# Extract book listings and save as JSON
python main.py \
  --url https://books.toscrape.com \
  --fields "title" "price" "rating" \
  --pages 5 --format json --output books.json

# Use Playwright for JavaScript-heavy sites
python main.py --url https://example-spa.com --fields "product" "price" --js
```

### CLI Options

| Option | Default | Description |
|---|---|---|
| `--url` | required | Starting URL |
| `--fields` | required | Fields to extract (space-separated) |
| `--pages` | 5 | Max pages to crawl |
| `--format` | csv | Output format: `csv`, `excel`, `json` |
| `--output` | results.csv | Output file path |
| `--js` | off | Use Playwright (JS sites) |
| `--delay` | 1.0 | Seconds between requests |
| `--all-domains` | off | Follow cross-domain links |

---

## 🗂️ Project Structure

```
Automated_AI_Web_Scrapper/
├── app.py                  # Streamlit chatbot UI ← start here
├── main.py                 # CLI entry point
├── config.py               # Environment config
├── requirements.txt
├── .env                    # Your API key (git-ignored)
├── scraper/
│   ├── crawler.py          # requests + BeautifulSoup
│   └── playwright_crawler.py
├── ai/
│   ├── extractor.py        # LangChain + Gemini chain
│   └── prompts.py
├── export/
│   └── exporter.py         # pandas → CSV/Excel/JSON
├── utils/
│   └── helpers.py
└── tests/
    ├── test_crawler.py
    ├── test_extractor.py
    └── test_exporter.py
```

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

No API key is needed — all LLM calls are mocked.

---

## ⚙️ How It Works

```
User (URL + question)
        │
        ▼
  Crawler (requests/Playwright)
        │  crawled pages [{url, text}]
        ▼
  AIExtractor (LangChain + Gemini)
        │  structured JSON
        ▼
  Streamlit Chat UI / Exporter
        │
        ▼
  Table in chat + CSV/Excel/JSON download
```
