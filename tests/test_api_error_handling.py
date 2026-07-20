from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from news_summarizer.app.main import app
from news_summarizer.database import repository
from news_summarizer.database import session as dbsession
from news_summarizer.database.models import Base
from tests.api_client import ASGITestClient


def setup_in_memory_db():
    engine = create_engine('sqlite:///:memory:', connect_args={"check_same_thread": False}, poolclass=StaticPool)
    dbsession.engine = engine
    dbsession.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(engine)


def test_missing_article_returns_404():
    setup_in_memory_db()
    response = ASGITestClient(app).get('/articles/999999')

    assert response.status_code == 404
    assert response.json()['detail'] == 'Article not found'


def test_unsupported_summarize_model_returns_400():
    response = ASGITestClient(app).post('/summarize', json={'text': 'short text', 'model': 'unknown'})

    assert response.status_code == 400
    assert 'Unsupported summarizer model' in response.json()['detail']


def test_unsupported_ingest_model_returns_400():
    response = ASGITestClient(app).post('/ingest', json={'limit': 0, 'models': ['unknown']})

    assert response.status_code == 400
    assert 'Unsupported summarizer model' in response.json()['detail']


def test_article_detail_returns_one_summary_per_model():
    setup_in_memory_db()
    db = dbsession.SessionLocal()
    article = repository.create_article(db, 'Article', 'http://example.com/article')
    first = repository.create_summary(db, article.id, 'tfidf', 'first summary', 'extractive', 0.1, 2)
    # Simulate old duplicated data that may already exist in a user's database.
    from news_summarizer.database.models import Summary
    duplicate = Summary(article_id=article.id, model_name='tfidf', summary_text='newest summary', summary_type='extractive', processing_time=0.2, summary_length=2)
    db.add(duplicate)
    db.commit()
    db.refresh(duplicate)
    repository.create_summary(db, article.id, 'textrank', 'textrank summary', 'extractive', 0.1, 2)
    article_id = article.id
    db.close()

    response = ASGITestClient(app).get(f'/articles/{article_id}')

    assert response.status_code == 200
    summaries = response.json()['summaries']
    assert [summary['model_name'] for summary in summaries].count('tfidf') == 1
    assert [summary['model_name'] for summary in summaries].count('textrank') == 1
    assert len(summaries) == 2


def test_create_summary_reuses_existing_model_summary():
    setup_in_memory_db()
    db = dbsession.SessionLocal()
    article = repository.create_article(db, 'Article', 'http://example.com/article')
    first = repository.create_summary(db, article.id, 'tfidf', 'first summary', 'extractive', 0.1, 2)
    second = repository.create_summary(db, article.id, 'tfidf', 'second summary', 'extractive', 0.2, 2)

    assert second.id == first.id
    assert len(repository.list_summaries(db)) == 1
    db.close()
