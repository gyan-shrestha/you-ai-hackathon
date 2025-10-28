import os
import re
import requests
from io import BytesIO
from PyPDF2 import PdfReader
import pdfplumber
from dotenv import load_dotenv
from pprint import pprint

# Load your API key
load_dotenv()
API_KEY = os.getenv("YOU_API_KEY")

HEADERS = {
    "X-API-Key": API_KEY,
    "Accept-Encoding": "gzip",
}

# Call You Search API
def test_search():
    url = "https://api.ydc-index.io/v1/search"
    params = {
        # Try searching only authoritative PDFs
        "query": "site:molinahealthcare.com +Molina +Silver +2025 +deductible filetype:pdf",
        "count": 5,
        "country": "US"
    }

    print("Searching You.com ...")
    r = requests.get(url, headers=HEADERS, params=params)
    print("STATUS:", r.status_code)
    if r.status_code != 200:
        print(r.text)
        return []

    data = r.json()
    results = data.get("results", {}).get("web", [])
    pdf_links = [res["url"] for res in results if res.get("url", "").lower().endswith(".pdf")]

    print(f"\nFound {len(pdf_links)} PDFs:")
    for i, link in enumerate(pdf_links):
        print(f"{i+1}. {link}")

    return pdf_links

def extract_text_from_pdf(pdf_url):
    print(f"\n Downloading PDF: {pdf_url}")
    resp = requests.get(pdf_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    
    # Check content type
    ctype = resp.headers.get("Content-Type", "")
    if "pdf" not in ctype.lower():
        print("This URL didn't return a PDF. It might be a redirect or HTML page.")
        print("Content-Type:", ctype)
        return ""
    
    # Ensure non-empty
    if len(resp.content) < 500:
        print("The PDF seems too small — likely not a valid file.")
        return ""

    # Use pdfplumber (more tolerant to real-world PDFs)
    try:
        with pdfplumber.open(BytesIO(resp.content)) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as e:
        print("pdfplumber failed, fallback to PyPDF2:", e)
        try:
            reader = PdfReader(BytesIO(resp.content))
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
        except Exception as e2:
            print("Both extractors failed:", e2)
            text = ""

    return text

# 4Use regex to find deductible values
def extract_deductibles(text):
    matches = re.findall(r"Deductible.*?\$[0-9,]+", text, flags=re.IGNORECASE)
    # Remove duplicates and clean whitespace
    return list(set([m.strip() for m in matches]))

# 5Main pipeline
def main():
    pdfs = test_search()
    if not pdfs:
        print("No PDF results found.")
        return

    # just use the first PDF for demo
    pdf_url = pdfs[0]
    text = extract_text_from_pdf(pdf_url)

    print("\n Extracting deductible values ...")
    deductibles = extract_deductibles(text)

    if deductibles:
        print("\n Deductibles Found:")
        for d in deductibles:
            print("-", d)
    else:
        print("\n No deductible values detected in this document.")

if __name__ == "__main__":
    main()
