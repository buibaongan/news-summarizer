from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import repository
from database import session as dbsession
from database.models import Base
from ingestion import ingest_pipeline
import ingestion.rss_collector as rc
import scraping.article_scraper as sc


class FailingSummarizer:
    model_name = 'failing-model'
    summary_type = 'abstractive'

    def summarize(self, text):
        raise RuntimeError('model unavailable')


def setup_in_memory_db():
    engine = create_engine('sqlite:///:memory:', connect_args={"check_same_thread": False}, poolclass=StaticPool)
    dbsession.engine = engine
    dbsession.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(engine)


def test_failed_summarizer_creates_fallback_summary(monkeypatch):
    setup_in_memory_db()
    monkeypatch.setattr(rc, 'collect_from_rss', lambda path='config/sources.json': [{
        'title': 'Fallback article',
        'url': 'http://example.com/fallback',
        'source': 'Example'
    }])
    monkeypatch.setattr(sc, 'scrape_article', lambda url: ('First sentence.\nSecond sentence.', 'mock', True))
    monkeypatch.setattr(ingest_pipeline, 'build_summarizers', lambda models=None: [FailingSummarizer()])

    stats = ingest_pipeline.ingest_all(models=['tfidf'])

    assert stats['summaries_created'] == 1
    assert stats['errors'][0]['model'] == 'failing-model'
    db = dbsession.SessionLocal()
    summaries = repository.list_summaries(db)
    assert summaries[0].model_name == 'failing-model'
    assert summaries[0].summary_type == 'abstractive_fallback'
    db.close()
