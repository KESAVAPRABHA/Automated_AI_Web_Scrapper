from langchain_core.prompts import PromptTemplate

EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["fields", "page_text", "url"],
    template="""You are an expert web data extraction assistant.

Your task: extract the following fields from the webpage content provided below.

URL: {url}
Fields to extract: {fields}

---WEBPAGE CONTENT START---
{page_text}
---WEBPAGE CONTENT END---

Rules:
1. Return ONLY a single valid JSON object — no markdown fences, no explanation.
2. Use the field names exactly as provided as JSON keys.
3. If a field has multiple values (e.g., multiple team members), return a JSON array.
4. If a field cannot be found on this page, set its value to null.
5. Never invent or hallucinate data — only extract what is explicitly present.

JSON output:""",
)


CHAT_PROMPT = PromptTemplate(
    input_variables=["user_query", "pages_summary", "url"],
    template="""You are an intelligent web extraction assistant helping a user analyse a website.

Loaded website: {url}

Crawled page content (multiple pages separated by ---):
{pages_summary}

User question: {user_query}

Instructions:
- Carefully read all the page content above.
- Return a JSON object with exactly two keys:
    "answer" : A concise, helpful conversational response (plain text, no markdown).
    "data"   : A list of relevant extracted records (list of dicts). Use [] if not applicable.
- If the user asks to extract structured data (names, prices, job openings, etc.),
  populate "data" with one dict per item, using sensible key names.
- If the user asks a yes/no or descriptive question, set "data" to [].
- Return ONLY valid JSON — no markdown fences, no extra text.

JSON output:""",
)


LINK_FILTER_PROMPT = PromptTemplate(
    input_variables=["fields", "links", "url"],
    template="""You are a web navigation expert.
A user wants to extract these fields: {fields}
From this website: {url}

Here is a list of links found on the homepage:
{links}

Based on the link text and URLs, which 3-5 links are MOST likely to contain the requested information?
Include the 'About', 'Team', 'Leadership', 'Careers', or 'Contact' pages if relevant to the fields.

Return ONLY a valid JSON list of strings (the absolute URLs).
Example: ["https://example.com/about", "https://example.com/team"]

JSON output:""",
)
