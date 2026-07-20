import json
import feedparser
from typing import List, Dict
from pathlib import Path

def load_sources(path: str = 'config/sources.json') -> List[Dict]:
    p = Path(path)
    if not p.exists():
        return []
    return json.loads(p.read_text())

def collect_from_rss(path: str = 'config/sources.json') -> List[Dict]:
    sources = load_sources(path)
    articles = []
    for s in sources:
        if not s.get('enabled', True):
            continue
        d = feedparser.parse(s['rss_url'])
        for entry in d.entries:
            articles.append({
                'title': entry.get('title'),
                'url': entry.get('link'),
                'source': s.get('name'),
                'published': entry.get('published') or entry.get('updated')
            })
    return articles
