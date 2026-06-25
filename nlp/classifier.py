KEYWORDS = {
    'technology': ['tech', 'software', 'ai', 'machine learning', 'computer'],
    'business': ['market', 'business', 'company', 'stock', 'economy'],
    'politics': ['government', 'election', 'policy', 'senate', 'congress'],
    'health': ['health', 'medical', 'covid', 'disease', 'hospital'],
    'sports': ['sport', 'game', 'tournament', 'team', 'score']
}

def classify_by_keywords(text: str) -> str:
    t = text.lower()
    for cat, kws in KEYWORDS.items():
        for k in kws:
            if k in t:
                return cat
    return 'other'
