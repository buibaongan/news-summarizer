import re


KEYWORDS = {
    'technology': ['technology', 'tech', 'software', 'artificial intelligence', 'ai', 'machine learning', 'computer'],
    'business': ['market', 'business', 'company', 'stock', 'economy'],
    'politics': ['government', 'election', 'policy', 'senate', 'congress'],
    'health': ['health', 'medical', 'covid', 'disease', 'hospital'],
    'sports': ['sport', 'sports', 'game', 'tournament', 'team', 'score'],
    'entertainment': ['entertainment', 'music', 'singer', 'actor', 'celebrity', 'wedding', 'film', 'movie']
}


def classify_by_keywords(text: str) -> str:
    t = (text or '').lower()
    scores = {}
    for cat, kws in KEYWORDS.items():
        scores[cat] = sum(1 for keyword in kws if _contains_keyword(t, keyword))

    best_category, best_score = max(scores.items(), key=lambda item: item[1])
    return best_category if best_score else 'other'


def _contains_keyword(text: str, keyword: str) -> bool:
    escaped = re.escape(keyword.lower())
    return re.search(rf'(?<![a-z0-9]){escaped}(?![a-z0-9])', text) is not None
