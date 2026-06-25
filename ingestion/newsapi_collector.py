import os
import requests
from typing import List, Dict

API_URL = 'https://newsapi.org/v2/top-headlines'

def collect_from_newsapi(api_key: str, params: dict = None) -> List[Dict]:
    if not api_key:
        return []
    params = params or {'language': 'en', 'pageSize': 100}
    params['apiKey'] = api_key
    r = requests.get(API_URL, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    articles = []
    for a in data.get('articles', []):
        articles.append({
            'title': a.get('title'),
            'url': a.get('url'),
            'source': a.get('source', {}).get('name'),
            'published': a.get('publishedAt')
        })
    return articles
