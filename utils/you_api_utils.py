import os
import requests
from dotenv import load_dotenv

load_dotenv()

YOU_API_KEY = os.getenv("YOU_API_KEY")
SEARCH_URL = "https://api.ydc-index.io/v1/search"
CONTENTS_URL = "https://api.ydc-index.io/v1/contents"
EXPRESS_URL = "https://api.you.com/v1/agents/runs"

HEADERS_SEARCH = {"X-API-Key": YOU_API_KEY}
HEADERS_CONTENTS = {"X-API-Key": YOU_API_KEY, "Content-Type": "application/json"}
HEADERS_EXPRESS = {"Authorization": f"Bearer {YOU_API_KEY}", "Content-Type": "application/json"}

# ---------------------------------------------------------------------
# Search API
# ---------------------------------------------------------------------
def search_pdfs(query: str, country="US", count=10):
    """
    You.com Search API for retrieving PDF results with metadata.
    Returns: list of dicts with {url, title, description, snippets}.
    """
    print(f"query: {query}")
    params = {"query": query, "count": count, "country": country}
    r = requests.get(SEARCH_URL, headers=HEADERS_SEARCH, params=params, timeout=30)

    if r.status_code != 200:
        print("Search error:", r.text)
        return []

    data = r.json()
    web_results = data.get("results", {}).get("web", [])
    pdf_results = []

    for res in web_results:
        url = res.get("url", "")
        if not url.lower().endswith(".pdf"):
            continue

        pdf_results.append({
            "url": url,
            "title": res.get("title", ""),
            "description": res.get("description", ""),
            "snippets": res.get("snippets", []),
        })

    print(f"Found {len(pdf_results)} PDF(s)")
    return pdf_results

# ---------------------------------------------------------------------
# Contents API
# ---------------------------------------------------------------------
def extract_via_contents_api(url: str, max_chars=2000):
    """Extracts text snippet from a PDF via You.com Contents API."""
    payload = {"urls": [url], "format": "markdown"}
    r = requests.post(CONTENTS_URL, headers=HEADERS_CONTENTS, json=payload, timeout=30)

    if r.status_code != 200:
        print("Contents API error:", r.text)
        return ""

    data = r.json()
    if isinstance(data, list) and len(data) > 0:
        content = data[0].get("markdown", "") or data[0].get("html", "")
        return content[:max_chars]
    return ""

# ---------------------------------------------------------------------
# Express Agent
# ---------------------------------------------------------------------
def ask_express_agent(context: str, question: str):
    """Ask You.com Express Agent to synthesize an answer, with fallback."""
    if context.strip():
        prompt = f"Answer the question based on this text:\n\n{context[:6000]}\n\nQuestion: {question}"
    else:
        prompt = (
            "The provided documents had no readable text. "
            "Please answer using your own knowledge and reliable 2025 insurance data.\n\n"
            f"Question: {question}"
        )

    payload = {"agent": "express", "input": prompt}
    r = requests.post(EXPRESS_URL, headers=HEADERS_EXPRESS, json=payload, timeout=60)

    if r.status_code != 200:
        print("Express Agent error:", r.text)
        return "Express Agent failed"

    data = r.json()
    output = data.get("output")
    if isinstance(output, list) and len(output) > 0:
        return output[0].get("text", "")
    return output if isinstance(output, str) else "No answer."
