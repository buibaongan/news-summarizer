from news_summarizer.database import session as dbsession
from news_summarizer.database.models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from news_summarizer.database import repository


def setup_db():
    engine = create_engine('sqlite:///:memory:', connect_args={"check_same_thread": False})
    dbsession.engine = engine
    dbsession.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(engine)
    return dbsession.SessionLocal()


def test_models_comparison_endpoint():
    db = setup_db()
    # create article and summaries and evaluation
    art = repository.create_article(db, title='T', url='http://x', source='X', full_text='text')
    s1 = repository.create_summary(db, art.id, 'tfidf', 'sum1', 'extractive', 0.1, 10)
    repository.create_evaluation_result(db, s1.id, rouge_1=0.5, rouge_2=0.2, rouge_l=0.4, bert_p=0.6, bert_r=0.5, bert_f=0.55)

    # query via direct DB aggregation similar to endpoint
    from sqlalchemy import func
    from news_summarizer.database.models import Summary, EvaluationResult
    row = db.query(Summary.model_name, func.count(Summary.id).label('num_summaries')).group_by(Summary.model_name).all()
    assert len(row) == 1
