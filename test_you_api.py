import os
import requests
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()
API_KEY = os.getenv("YOU_API_KEY")

HEADERS = {
    "X-API-Key": API_KEY,     
    "Accept-Encoding": "gzip",  
}

def test_search():
    url = "https://api.ydc-index.io/v1/search"
    # params = {
    #     "query": "deductible for molina silver 2025",
    #     "count": 3
    # }

    # API usage link: https://documentation.you.com/api-reference/search#authorization-x-api-key
    # API usage link: https://documentation.you.com/developer-resources/search-operators
    params = {
        "query": "site:molinahealthcare.com + site:healthcare.gov +Molina +Silver +2025 +deductible filetype:pdf",
        # "query": "Molina Silver 1 HMO 2025 deductible site:molinahealthcare.com filetype:pdf lang:es site:healthcare.gov",
        "count": 3,
        "country": "US"
    }
    r = requests.get(url, headers=HEADERS, params=params)
    print("STATUS:", r.status_code)
    print("URL CALLED:", r.url)
    print("\nResponse Text:")
    try:
        pprint(r.json())
    except Exception:
        print(r.text)

if __name__ == "__main__":
    test_search()

