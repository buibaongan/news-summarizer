from news_summarizer.ingestion.rss_collector import collect_from_rss

def test_collect_rss():
    res = collect_from_rss('config/sources.json')
    assert isinstance(res, list)
