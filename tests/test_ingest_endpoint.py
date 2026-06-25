import os
from app.main import app
from tests.api_client import ASGITestClient
import ingestion.rss_collector as rc
import scraping.article_scraper as sc
from database import session as dbsession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from database.models import Base


def setup_in_memory_db():
    engine = create_engine('sqlite:///:memory:', connect_args={"check_same_thread": False}, poolclass=StaticPool)
    dbsession.engine = engine
    dbsession.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(engine)


def test_ingest_endpoint(monkeypatch):
    setup_in_memory_db()

    # mock RSS collector to return one article
    monkeypatch.setattr(rc, 'collect_from_rss', lambda path='config/sources.json': [{'title': 'Test Article', 'url': 'http://example.com/test', 'source': 'Example', 'published': '2026-01-01'}])
    # mock scraper to return text
    monkeypatch.setattr(sc, 'scrape_article', lambda url: ('This is the full article text about testing.', 'mock', True))

    client = ASGITestClient(app)
    r = client.post('/ingest')
    assert r.status_code == 200
    data = r.json()
    assert data['saved_articles'] == 1
    assert data['summaries_created'] >= 3
