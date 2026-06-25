from database import session as dbsession
from database.models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ingestion.dedup import normalize_title, is_duplicate


def setup_db():
    engine = create_engine('sqlite:///:memory:', connect_args={"check_same_thread": False})
    dbsession.engine = engine
    dbsession.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(engine)
    return dbsession.SessionLocal()


def test_normalize_title():
    assert normalize_title('Hello, World!') == 'hello world'


def test_is_duplicate_by_url():
    db = setup_db()
    from database.repository import create_article
    a = create_article(db, title='A', url='http://example.com/1')
    assert is_duplicate(db, 'http://example.com/1', 'A')
