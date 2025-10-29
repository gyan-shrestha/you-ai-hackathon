import json, os

# cache pdf so it can be fetched after ranking for context based QA with LLM
CACHE_PATH = "pdf_text_cache.json"

def load_cache():
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)

def get_or_fetch(url, fetch_fn, max_chars=20000):
    """Load cached text if available, otherwise fetch and store."""
    cache = load_cache()
    if url in cache and cache[url].strip():
        print(f"Cached: {url}")
        return cache[url]
    print(f"Fetching: {url}")
    text = fetch_fn(url, max_chars=max_chars)
    if text.strip():
        cache[url] = text
        save_cache(cache)
    return text
