import os
import numpy as np
from rank_bm25 import BM25Okapi
from voyageai import Client

from dotenv import load_dotenv
load_dotenv()
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
vclient = Client(api_key=VOYAGE_API_KEY)

# ---------------------------------------------------------
# BM25 lexical reranker
# ---------------------------------------------------------
def rerank_bm25(user_query: str, pdf_results: list, top_k: int = 3):
    """
    pdf_results: list of dicts with title, description, snippets, url
    Returns top_k by lexical relevance.
    """
    docs = []
    for r in pdf_results:
        combined = " ".join([
            r.get("title", ""),
            r.get("description", ""),
            " ".join(r.get("snippets", []))
        ])
        docs.append(combined)

    tokenized = [d.lower().split() for d in docs]
    bm25 = BM25Okapi(tokenized)
    scores = bm25.get_scores(user_query.lower().split())

    ranked = sorted(zip(pdf_results, scores), key=lambda x: -x[1])
    print(f"BM25 top {top_k} URLs:")
    for r, s in ranked[:top_k]:
        print(f"  {r['url']}  (score={s:.2f})")
    return [r for r, _ in ranked[:top_k]]

# ---------------------------------------------------------
# VoyageAI embedding reranker
# ---------------------------------------------------------
def rerank_voyage(user_query: str, candidates: list, cache: dict, top_k: int = 1):
    """
    candidates: list of pdf result dicts (top_k from BM25)
    cache: {url: text}
    Returns top_k reranked by cosine similarity.
    """
    q_emb = vclient.embed(texts=[user_query], model="voyage-large-2").embeddings[0]

    sims = []

    for r in candidates:
        url = r["url"]
        content = cache.get(url)
        if not content:
            continue
        d_emb = vclient.embed(texts=[content[:4000]], model="voyage-large-2").embeddings[0]
        cos_sim = np.dot(q_emb, d_emb) / (np.linalg.norm(q_emb) * np.linalg.norm(d_emb))
        sims.append((r, cos_sim))

    sims = sorted(sims, key=lambda x: -x[1])
    print("VoyageAI similarity scores:")
    for r, s in sims:
        print(f"  {r['url']}  (cos={s:.3f})")
        print(f"  {r['title']}  (cos={s:.3f})")
    return [r for r, _ in sims[:top_k]]
