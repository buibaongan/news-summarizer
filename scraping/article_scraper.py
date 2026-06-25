from typing import Tuple

def scrape_article(url: str) -> Tuple[str, str, bool]:
    """Try trafilatura first, fallback to BeautifulSoup. Returns (text, method, success)."""
    try:
        import trafilatura

        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded)
            if text:
                return text, 'trafilatura', True
    except Exception:
        pass

    # fallback
    try:
        import requests
        from bs4 import BeautifulSoup

        r = requests.get(url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        article = soup.find('article')
        if article:
            txt = article.get_text(separator='\n').strip()
        else:
            txt = soup.get_text(separator='\n').strip()
        return txt, 'beautifulsoup', True if txt else False
    except Exception:
        return '', 'failed', False
