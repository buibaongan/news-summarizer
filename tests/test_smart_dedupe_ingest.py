from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from news_summarizer.app.main import app
from tests.api_client import ASGITestClient
from news_summarizer.database import repository
from news_summarizer.database import session as dbsession
from news_summarizer.database.models import Base
import news_summarizer.ingestion.rss_collector as rc
import news_summarizer.scraping.article_scraper as sc


def setup_in_memory_db():
    engine = create_engine('sqlite:///:memory:', connect_args={"check_same_thread": False}, poolclass=StaticPool)
    dbsession.engine = engine
    dbsession.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(engine)


def seed_article(title='Market Rally Today', url='http://example.com/original', summary_model=None):
    db = dbsession.SessionLocal()
    article = repository.create_article(db, title=title, url=url, source='Seed', full_text='old text')
    if summary_model:
        repository.create_summary(db, article.id, summary_model, 'old summary', 'extractive', 0.1, 2)
    db.close()
    return article


def test_ingest_skips_duplicate_by_url(monkeypatch):
    setup_in_memory_db()
    seed_article(summary_model='tfidf')
    monkeypatch.setattr(rc, 'collect_from_rss', lambda path='config/sources.json': [{'title': 'Anything', 'url': 'http://example.com/original', 'source': 'BBC'}])

    response = ASGITestClient(app).post('/ingest', json={'models': ['tfidf']})

    assert response.status_code == 200
    assert response.json()['skipped_duplicates'] == 1


def test_ingest_skips_duplicate_by_normalized_title(monkeypatch):
    setup_in_memory_db()
    seed_article(title='Market Rally Today', summary_model='tfidf')
    monkeypatch.setattr(rc, 'collect_from_rss', lambda path='config/sources.json': [{'title': 'Market: Rally Today!', 'url': 'http://example.com/new', 'source': 'BBC'}])

    response = ASGITestClient(app).post('/ingest', json={'models': ['tfidf']})

    assert response.status_code == 200
    assert response.json()['skipped_duplicates'] == 1


def test_ingest_skips_duplicate_by_title_similarity(monkeypatch):
    setup_in_memory_db()
    seed_article(title='Government announces new climate policy today', summary_model='tfidf')
    monkeypatch.setattr(rc, 'collect_from_rss', lambda path='config/sources.json': [{'title': 'Government announces new climate policy', 'url': 'http://example.com/similar', 'source': 'BBC'}])

    response = ASGITestClient(app).post('/ingest', json={'models': ['tfidf']})

    assert response.status_code == 200
    assert response.json()['skipped_duplicates'] == 1


def test_force_refresh_updates_duplicate_and_summarizes(monkeypatch):
    setup_in_memory_db()
    seed_article(title='Old Title', url='http://example.com/original')
    monkeypatch.setattr(rc, 'collect_from_rss', lambda path='config/sources.json': [{'title': 'Old Title', 'url': 'http://example.com/original', 'source': 'BBC'}])
    monkeypatch.setattr(sc, 'scrape_article', lambda url: ('new article text', 'mock', True))

    response = ASGITestClient(app).post('/ingest', json={'force_refresh': True, 'models': ['tfidf']})

    assert response.status_code == 200
    data = response.json()
    assert data['skipped_duplicates'] == 0
    assert data['summaries_created'] == 1
    db = dbsession.SessionLocal()
    updated = repository.get_article_by_url(db, 'http://example.com/original')
    assert updated.full_text == 'new article text'
    db.close()


def test_ingest_skips_existing_model_summary(monkeypatch):
    setup_in_memory_db()
    article = seed_article(title='Existing Summary', url='http://example.com/original')
    db = dbsession.SessionLocal()
    repository.create_summary(db, article.id, 'tfidf', 'old summary', 'extractive', 0.1, 2)
    db.close()
    monkeypatch.setattr(rc, 'collect_from_rss', lambda path='config/sources.json': [{'title': 'Existing Summary', 'url': 'http://example.com/original', 'source': 'BBC'}])
    monkeypatch.setattr(sc, 'scrape_article', lambda url: ('new article text\nsecond line', 'mock', True))

    response = ASGITestClient(app).post('/ingest', json={'force_refresh': True, 'models': ['tfidf', 'textrank']})

    assert response.status_code == 200
    data = response.json()
    assert data['skipped_existing_summaries'] == 1
    assert data['summaries_created'] == 1
    db = dbsession.SessionLocal()
    updated = repository.get_article_by_url(db, 'http://example.com/original')
    summaries = repository.list_summaries(db)
    assert updated.full_text == 'new article text\nsecond line'
    assert [summary.model_name for summary in summaries].count('tfidf') == 1
    assert [summary.model_name for summary in summaries].count('textrank') == 1
    db.close()


def test_duplicate_article_adds_missing_model_summary(monkeypatch):
    setup_in_memory_db()
    seed_article(title='Existing Summary', url='http://example.com/original', summary_model='tfidf')
    monkeypatch.setattr(rc, 'collect_from_rss', lambda path='config/sources.json': [{'title': 'Existing Summary', 'url': 'http://example.com/original', 'source': 'BBC'}])
    monkeypatch.setattr(sc, 'scrape_article', lambda url: (_ for _ in ()).throw(AssertionError('should use stored article text')))

    response = ASGITestClient(app).post('/ingest', json={'models': ['tfidf', 'textrank']})

    assert response.status_code == 200
    data = response.json()
    assert data['skipped_duplicates'] == 0
    assert data['skipped_existing_summaries'] == 1
    assert data['summaries_created'] == 1
    db = dbsession.SessionLocal()
    article = repository.get_article_by_url(db, 'http://example.com/original')
    summaries = db.query(repository.Summary).filter(repository.Summary.article_id == article.id).all()
    assert [summary.model_name for summary in summaries].count('tfidf') == 1
    assert [summary.model_name for summary in summaries].count('textrank') == 1
    db.close()


def test_ingest_backfills_missing_summaries_for_existing_articles_not_in_feed(monkeypatch):
    setup_in_memory_db()
    seed_article(title='Old Stored Article', url='http://example.com/old', summary_model='tfidf')
    monkeypatch.setattr(rc, 'collect_from_rss', lambda path='config/sources.json': [])

    response = ASGITestClient(app).post('/ingest', json={'models': ['tfidf', 'textrank']})

    assert response.status_code == 200
    data = response.json()
    assert data['collected'] == 0
    assert data['backfilled_summaries'] == 1
    assert data['skipped_existing_summaries'] == 0
    db = dbsession.SessionLocal()
    article = repository.get_article_by_url(db, 'http://example.com/old')
    summaries = db.query(repository.Summary).filter(repository.Summary.article_id == article.id).all()
    assert [summary.model_name for summary in summaries].count('tfidf') == 1
    assert [summary.model_name for summary in summaries].count('textrank') == 1
    db.close()
