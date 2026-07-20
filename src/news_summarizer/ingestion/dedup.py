import re
from difflib import SequenceMatcher
from news_summarizer.database.models import Article

def normalize_title(title: str) -> str:
    t = title.lower()
    t = re.sub(r"[^a-z0-9\s]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

def is_duplicate(db, url: str, title: str, threshold: float = 0.85) -> bool:
    # check exact url
    if db.query(Article).filter(Article.url == url).first():
        return True
    norm = normalize_title(title)
    # exact normalized title
    existing = db.query(Article).all()
    for e in existing:
        if normalize_title(e.title) == norm:
            return True
        if similarity(norm, normalize_title(e.title)) >= threshold:
            return True
    return False
