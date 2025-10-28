
import os
import re
import requests
from io import BytesIO
from pprint import pprint
import pdfplumber
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import numpy as np

# -------------------------
# 1. Load API key & configs
# -------------------------
load_dotenv()
API_KEY = os.getenv("YOU_API_KEY")

HEADERS = {
    "X-API-Key": API_KEY,
    "Accept-Encoding": "gzip",
}

# Load local embedding model
print(" Loading embedding model (MiniLM)...")
model = SentenceTransformer("all-MiniLM-L6-v2")

# -------------------------
# 2. Embedding utilities
# -------------------------
def embed(text: str):
    """Get normalized embedding vector for a text."""
    emb = model.encode(text, normalize_embeddings=True)
    return emb

def cosine(a, b):
    return np.dot(a, b)

def rerank_results(results, query, top_k=3):
    """Rerank You.com results by semantic similarity."""
    q_emb = embed(query)
    scored = []
    for res in results:
        text = f"{res.get('title','')} {res.get('description','')}"
        emb = embed(text)
        sim = cosine(q_emb, emb)
        scored.append((sim, res))
    scored.sort(key=lambda x: x[0], reverse=True)
    reranked = [r for _, r in scored[:top_k]]
    print(f"\n Reranked top {top_k} results by embedding similarity:")
    for i, r in enumerate(reranked, 1):
        print(f"{i}. {r.get('title','N/A')} ({r.get('url','')})")
    return reranked

# -------------------------
# 3. You.com Search
# -------------------------
def test_search():
    url = "https://api.ydc-index.io/v1/search"
    params = {
        "query": "site:molinahealthcare.com +Molina +Silver +2025 +deductible filetype:pdf",
        "count": 10,
        "country": "US",
    }

    print("\n Searching You.com ...")
    r = requests.get(url, headers=HEADERS, params=params)
    print("STATUS:", r.status_code)
    if r.status_code != 200:
        print(r.text)
        return []

    data = r.json()
    results = data.get("results", {}).get("web", [])
    if not results:
        print("No results found.")
        return []

    # Rerank results by semantic similarity
    reranked = rerank_results(results, params["query"], top_k=3)

    pdf_links = [
        res["url"]
        for res in reranked
        if res.get("url", "").lower().endswith(".pdf")
    ]

    if not pdf_links:
        print(" No direct PDF links found after reranking.")
    else:
        print(f"\n Found {len(pdf_links)} PDF(s):")
        for i, link in enumerate(pdf_links):
            print(f"{i+1}. {link}")

    return pdf_links

# -------------------------
# 4. PDF text extraction
# -------------------------
def extract_text_from_pdf(pdf_url):
    print(f"\n Downloading PDF: {pdf_url}")
    try:
        resp = requests.get(pdf_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    except Exception as e:
        print("Failed to download:", e)
        return ""

    ctype = resp.headers.get("Content-Type", "")
    if "pdf" not in ctype.lower():
        print("This URL didn't return a PDF. It might be a redirect or HTML page.")
        print("Content-Type:", ctype)
        return ""

    if len(resp.content) < 500:
        print("The PDF seems too small — likely not valid.")
        return ""

    text = ""
    try:
        with pdfplumber.open(BytesIO(resp.content)) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as e:
        print("pdfplumber failed, fallback to PyPDF2:", e)
        try:
            reader = PdfReader(BytesIO(resp.content))
            for page in reader.pages:
                text += page.extract_text() or ""
        except Exception as e2:
            print("Both extractors failed:", e2)
            text = ""

    return text

# -------------------------
# 5. Deductible extraction
# -------------------------
def extract_deductibles(text):
    matches = re.findall(r"Deductible.*?\$[0-9,]+", text, flags=re.IGNORECASE)
    return list(set([m.strip() for m in matches]))

# -------------------------
# 6. Main pipeline
# -------------------------
def main():
    pdfs = test_search()
    if not pdfs:
        print("No PDF results found.")
        return

    pdf_url = pdfs[0]
    text = extract_text_from_pdf(pdf_url)

    print("\n Extracting deductible values ...")
    deductibles = extract_deductibles(text)

    if deductibles:
        print("\n Deductibles Found:")
        for d in deductibles:
            print("-", d)
    else:
        print("\n⚠️ No deductible values detected in this document.")

if __name__ == "__main__":
    main()
