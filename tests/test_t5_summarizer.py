from news_summarizer.ingestion.ingest_pipeline import build_summarizers


def test_build_summarizers_includes_t5():
    summarizers = build_summarizers(['tfidf', 't5'])

    assert [s.model_name for s in summarizers] == ['tfidf', 't5-small']
