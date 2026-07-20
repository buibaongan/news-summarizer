import os
from news_summarizer.app.main import app
from tests.api_client import ASGITestClient
import news_summarizer.ingestion.rss_collector as rc
import news_summarizer.scraping.article_scraper as sc
from news_summarizer.database import session as dbsession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from news_summarizer.database.models import Base
from news_summarizer.database import repository


def setup_in_memory_db():
    engine = create_engine('sqlite:///:memory:', connect_args={"check_same_thread": False}, poolclass=StaticPool)
    dbsession.engine = engine
    dbsession.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(engine)


def test_ingest_limit_and_source(monkeypatch):
    setup_in_memory_db()
    # create two mock articles with different sources
    articles = [
        {'title': 'A1', 'url': 'http://example.com/1', 'source': 'BBC', 'published': '2026-01-01'},
        {'title': 'A2', 'url': 'http://example.com/2', 'source': 'Reuters', 'published': '2026-01-02'},
    ]
    monkeypatch.setattr(rc, 'collect_from_rss', lambda path='config/sources.json': articles)
    monkeypatch.setattr(sc, 'scrape_article', lambda url: ('full text', 'mock', True))

    client = ASGITestClient(app)
    r = client.post('/ingest', json={'limit': 1, 'source': 'BBC', 'force_refresh': False})
    assert r.status_code == 200
    data = r.json()
    assert data['collected'] == 1
    assert data['saved_articles'] == 1


def test_ingest_force_refresh(monkeypatch):
    setup_in_memory_db()
    # create initial article
    db = dbsession.SessionLocal()
    art = repository.create_article(db, title='Old', url='http://example.com/old', source='BBC', full_text='old')
    db.close()

    monkeypatch.setattr(rc, 'collect_from_rss', lambda path='config/sources.json': [{'title': 'Old', 'url': 'http://example.com/old', 'source': 'BBC', 'published': '2026-01-01'}])
    monkeypatch.setattr(sc, 'scrape_article', lambda url: ('new full text', 'mock', True))

    client = ASGITestClient(app)
    r = client.post('/ingest', json={'limit': 1, 'source': 'BBC', 'force_refresh': True})
    assert r.status_code == 200
    data = r.json()
    assert data['saved_articles'] == 0 or data['saved_articles'] == 1
    # ensure article full_text updated
    db = dbsession.SessionLocal()
    updated = repository.get_article_by_url(db, 'http://example.com/old')
    assert updated.full_text == 'new full text'
    db.close()
