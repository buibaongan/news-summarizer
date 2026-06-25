from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Article(Base):
    __tablename__ = 'articles'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False)
    source = Column(String)
    published_at = Column(String)
    full_text = Column(Text)
    category = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    summaries = relationship('Summary', back_populates='article')

class Summary(Base):
    __tablename__ = 'summaries'
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('articles.id'))
    model_name = Column(String)
    summary_text = Column(Text)
    summary_type = Column(String)
    processing_time = Column(Float)
    summary_length = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_to_telegram = Column(Boolean, default=False)
    article = relationship('Article', back_populates='summaries')

class EvaluationResult(Base):
    __tablename__ = 'evaluation_results'
    id = Column(Integer, primary_key=True)
    summary_id = Column(Integer, ForeignKey('summaries.id'))
    rouge_1 = Column(Float)
    rouge_2 = Column(Float)
    rouge_l = Column(Float)
    bertscore_precision = Column(Float)
    bertscore_recall = Column(Float)
    bertscore_f1 = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class Source(Base):
    __tablename__ = 'sources'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    rss_url = Column(String)
    enabled = Column(Boolean, default=True)
