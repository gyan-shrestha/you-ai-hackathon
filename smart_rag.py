"""
smart_rag.py
Hybrid two-stage retrieval pipeline: You.com, semantic reranking, express agent
"""

from query_builder import build_and_search
from utils.you_api_utils import extract_via_contents_api, ask_express_agent
from utils.cache_utils import get_or_fetch
from utils.rank_utils import bm25_scores, semantic_scores, hybrid_scores, topk_by
import re


# Stopword-based Query Cleaner
STOPWORDS = {
    "what","is","the","for","in","of","a","an","to","on","and","or",
    "by","at","from","about","this","that","which","who","where","how",
    "when","does","do","did","are","was","were","be","have","has","had",
    "can","could","should","would","will","may","might"
}

def clean_query(text: str) -> str:
    """Remove stopwords and punctuation from user query."""
    words = re.findall(r"\b\w+\b", text.lower())
    filtered = [w for w in words if w not in STOPWORDS]
    return " ".join(filtered)


def clean_extracted_text(raw: str) -> str:
    """Clean noisy extracted text from You.com Contents API."""
    text = raw
    # Remove markdown and HTML artifacts
    text = re.sub(r"<[^>]+>", " ", text)       # remove HTML tags
    text = re.sub(r"\|+", " ", text)           # remove markdown table pipes
    text = re.sub(r"[-*_]{2,}", " ", text)     # remove table separators
    text = re.sub(r"\\n+", " ", text)          # remove escaped newlines
    text = re.sub(r"\s{2,}", " ", text)        # normalize spaces
    text = re.sub(r"(Free\s*){3,}", "Free ", text, flags=re.IGNORECASE)
    # Keep only readable chars
    text = re.sub(r"[^A-Za-z0-9$.,%/()\-\s]+", " ", text)
    return text.strip()


#  Combine title, desc, snippets
def _meta_text(r):
    """Concatenate title, description, and snippets for ranking."""
    return (r.get("title", "") + r.get("description", ""))


# Main Pipeline
def run_pipeline(user_question: str, top_k_search: int = 5, w_meta: float = 0.5, w_content: float = 0.5):
    print(" USER QUESTION:", user_question)

    # --- Stage 1: Search PDFs ---
    query, pdf_results = build_and_search(user_question)
    if not pdf_results:
        print("No PDFs found. Using Express Agent directly.")
        print(ask_express_agent("", user_question))
        return

    # Take top 5 from You.com search
    pdf_results = pdf_results[:top_k_search]
    print(f"Taking top {len(pdf_results)} PDFs from You.com search.")
    print("ALL Original Search Results (before ranking)]")
    for i, r in enumerate(pdf_results, 1):
        print(f"{i}. URL: {r['url']}")
        print(f"   Title: {r.get('title','')[:120]}")

    # --- Stage 2: Semantic on metadata ---
    user_question = clean_query(user_question)
    meta_docs = [_meta_text(r) for r in pdf_results]
    sem_meta = semantic_scores(user_question, meta_docs)

    print("\n[Metadata Semantic Scores]")
    for i, r in enumerate(pdf_results, 1):
        print(f"{i}. {r['url']}")
        print(f"   Title: {r.get('title','')[:100]}")
        print(f"   SEM_META={sem_meta[i-1]:.3f}")

    # --- Stage 3: Semantic on PDF full content ---
    docs = []
    full_texts = []
    for r in pdf_results:
        url = r["url"]
        text = get_or_fetch(url, extract_via_contents_api, max_chars=20000)
        text = clean_extracted_text(text)
        if text.strip():
            docs.append((url, text))
            full_texts.append(text)
        else:
            full_texts.append("")

    sem_content = semantic_scores(user_question, full_texts)

    print("\n[Content Semantic Scores]")
    for i, r in enumerate(pdf_results, 1):
        print(f"{i}. {r['url']}")
        print(f"   SEM_CONTENT={sem_content[i-1]:.3f}")

    # --- Hybrid score ---
    hybrid_scores = [w_meta * sem_meta[i] + w_content * sem_content[i] for i in range(len(pdf_results))]

    # --- Select best PDF(s) ---
    doc_items = [{"url": r["url"], "text": docs[i][1] if i < len(docs) else ""} for i, r in enumerate(pdf_results)]
    top_docs = topk_by(hybrid_scores, doc_items, k=1)
    best_doc = top_docs[0]

    print(" [Hybrid Semantic Ranking — Top Result]")
    idx = pdf_results.index(next(r for r in pdf_results if r["url"] == best_doc["url"]))
    print(f"{best_doc['url']}")
    print(f"META={sem_meta[idx]:.3f} | CONTENT={sem_content[idx]:.3f} | HYBRID={hybrid_scores[idx]:.3f}")

    # --- Generate answer ---
    context = best_doc["text"][:8000]
    answer = ask_express_agent(context, user_question)

    print(" FINAL ANSWER:\n", answer)
    print("==============================")
    print(" SOURCE:\n -", best_doc["url"])


if __name__ == "__main__":
    q = input("Enter your question: ").strip() or \
        "What is the deductible for Molina Silver 1 HMO 2025 in Florida?"
    run_pipeline(q)
