"""
smart_rag.py
Full retrieval pipeline: You.com, BM25 ranking, VoyageAI embeddibg reranking, Express Agent
"""

from query_builder import build_and_search
from utils.you_api_utils import extract_via_contents_api, ask_express_agent
from utils.rank_utils import rerank_bm25, rerank_voyage
from utils.cache_utils import load_cache, save_cache

def run_pipeline(user_question: str):
    print("\n==============================")
    print(" USER QUESTION:", user_question)
    print("==============================")

    query, pdfs = build_and_search(user_question)
    if not pdfs:
        answer = ask_express_agent("", user_question)
        # print("No PDFs found.")
        # return

    # Load local cache
    cache = load_cache()

    # BM25 lexical rerank
    top3 = rerank_bm25(user_question, pdfs, top_k=3)


    # Fetch + cache contents for Voyage rerank
    for r in top3:
        url = r["url"]
        if url not in cache:
            print(f"Fetching content for {url}")
            cache[url] = extract_via_contents_api(url, max_chars=8000)
    save_cache(cache)
 
    # VoyageAI embedding semantic rerank
    top1 = rerank_voyage(user_question, top3, cache, top_k=1)
    best = top1[0] if top1 else top3[0]
    best_url = best["url"]
    combined_context = cache.get(best_url, "")
    answer = ask_express_agent(combined_context, user_question)

    print("\n==============================")
    print(" FINAL ANSWER:\n", answer)
    print("==============================")
    print(" SOURCE(S):")
    print("best_url: ", best_url)

if __name__ == "__main__":
    q = input("Enter your question: ").strip()
    if not q:
        q = "What is the deductible for Molina Silver 1 HMO 2025 in Florida?"
    run_pipeline(q)
