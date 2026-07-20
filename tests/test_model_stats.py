from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from news_summarizer.app.main import app
from tests.api_client import ASGITestClient
from news_summarizer.database import repository
from news_summarizer.database import session as dbsession
from news_summarizer.database.models import Base


def setup_db():
    engine = create_engine('sqlite:///:memory:', connect_args={"check_same_thread": False}, poolclass=StaticPool)
    dbsession.engine = engine
    dbsession.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(engine)
    return dbsession.SessionLocal()


def seed_stats():
    db = setup_db()
    article = repository.create_article(db, title='T', url='http://stats', source='X', full_text='text')
    summary = repository.create_summary(db, article.id, 'tfidf', 'summary text', 'extractive', 0.2, 2)
    repository.create_evaluation_result(db, summary.id, rouge_1=0.4, rouge_2=0.2, rouge_l=0.3, bert_f=0.5)
    return db


def test_repository_model_stats():
    db = seed_stats()

    stats = repository.get_model_stats(db)

    assert stats['total_articles'] == 1
    assert stats['total_summaries'] == 1
    assert stats['summaries_by_model'][0]['model_name'] == 'tfidf'
    assert stats['summaries_by_model'][0]['average_rouge_1'] == 0.4
    db.close()


def test_models_stats_endpoint():
    db = seed_stats()
    db.close()

    response = ASGITestClient(app).get('/models/stats')

    assert response.status_code == 200
    data = response.json()
    assert data['total_articles'] == 1
    assert data['summaries_by_model'][0]['average_bertscore_f1'] == 0.5
