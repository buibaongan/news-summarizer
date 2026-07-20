from fastapi import APIRouter

from news_summarizer.ingestion.rss_collector import load_sources

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("")
async def list_sources():
    sources = load_sources('config/sources.json')
    return [
        {
            'name': source.get('name'),
            'rss_url': source.get('rss_url'),
            'enabled': source.get('enabled', True)
        }
        for source in sources
    ]
