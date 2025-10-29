"""
smart_rag.py
"""

from query_builder import build_and_search
from utils.you_api_utils import extract_via_contents_api, ask_express_agent

def run_pipeline(user_question: str):
    print("\n==============================")
    print(" USER QUESTION:", user_question)
    print("==============================")

    query, pdfs = build_and_search(user_question)
    if not pdfs:
        print("No PDFs found.")
        return

    # TODO: if we wnat to do some pdf ranking to get top ranked pdf for content search
    top_pdfs = pdfs[:1]

    combined_context = ""
    for url in top_pdfs:
        context = extract_via_contents_api(url, max_chars=8000)
        combined_context += f"\n\nFrom {url}:\n{context}\n"

    answer = ask_express_agent(combined_context, user_question)

    print("\n==============================")
    print(" FINAL ANSWER:\n", answer)
    print("==============================")
    print(" SOURCE(S):")
    for url in top_pdfs:
        print(" -", url)

if __name__ == "__main__":
    q = input("Enter your question: ").strip()
    if not q:
        q = "What is the deductible for Molina Silver 1 HMO 2025 in Florida?"
    run_pipeline(q)
