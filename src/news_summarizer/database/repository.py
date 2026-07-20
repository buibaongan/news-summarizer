from news_summarizer.database.session import SessionLocal
from news_summarizer.database.models import Article, Summary, EvaluationResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from news_summarizer.ingestion.dedup import normalize_title, similarity

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_article(db, title, url, source=None, published_at=None, full_text=None, category=None):
    a = Article(title=title, url=url, source=source, published_at=published_at, full_text=full_text, category=category)
    db.add(a)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return db.query(Article).filter(Article.url == url).first()
    db.refresh(a)
    return a

def get_article(db, article_id):
    return db.query(Article).filter(Article.id == article_id).first()

def get_article_by_url(db, url: str):
    return db.query(Article).filter(Article.url == url).first()

def get_article_by_normalized_title(db, normalized_title: str):
    for article in db.query(Article).all():
        if normalize_title(article.title or '') == normalized_title:
            return article
    return None

def list_existing_titles(db):
    return [row[0] for row in db.query(Article.title).all() if row[0]]

def find_duplicate_article(db, url: str, title: str, threshold: float = 0.85):
    if url:
        existing = get_article_by_url(db, url)
        if existing:
            return existing

    normalized = normalize_title(title or '')
    if normalized:
        existing = get_article_by_normalized_title(db, normalized)
        if existing:
            return existing

        for article in db.query(Article).all():
            if similarity(normalized, normalize_title(article.title or '')) >= threshold:
                return article
    return None

def update_article_full_text(db, article_id: int, full_text: str):
    a = db.query(Article).filter(Article.id == article_id).first()
    if a:
        a.full_text = full_text
        db.commit()
        db.refresh(a)
    return a

def list_articles(db, limit=50):
    return db.query(Article).order_by(Article.created_at.desc()).limit(limit).all()

def list_articles_for_backfill(db, source=None):
    query = db.query(Article).filter(Article.full_text.isnot(None), Article.full_text != '')
    if source:
        query = query.filter(func.lower(Article.source) == source.lower())
    return query.order_by(Article.created_at.desc()).all()

def create_summary(db, article_id, model_name, summary_text, summary_type, processing_time, summary_length):
    existing = get_summary_by_article_and_model(db, article_id, model_name)
    if existing:
        return existing
    s = Summary(article_id=article_id, model_name=model_name, summary_text=summary_text, summary_type=summary_type, processing_time=processing_time, summary_length=summary_length)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s

def get_summary_by_article_and_model(db, article_id, model_name):
    return db.query(Summary).filter(
        Summary.article_id == article_id,
        Summary.model_name == model_name
    ).order_by(Summary.created_at.desc()).first()

def list_summaries(db, limit=100):
    return db.query(Summary).order_by(Summary.created_at.desc()).limit(limit).all()

def get_unsent_summaries(db):
    return db.query(Summary).filter(Summary.sent_to_telegram == False).all()

def mark_summary_sent(db, summary_id):
    s = db.query(Summary).filter(Summary.id == summary_id).first()
    if s:
        s.sent_to_telegram = True
        db.commit()
    return s

def create_evaluation_result(db, summary_id, rouge_1=None, rouge_2=None, rouge_l=None, bert_p=None, bert_r=None, bert_f=None):
    er = EvaluationResult(summary_id=summary_id, rouge_1=rouge_1, rouge_2=rouge_2, rouge_l=rouge_l, bertscore_precision=bert_p, bertscore_recall=bert_r, bertscore_f1=bert_f)
    db.add(er)
    db.commit()
    db.refresh(er)
    return er

def get_model_stats(db):
    total_articles = db.query(func.count(Article.id)).scalar() or 0
    total_summaries = db.query(func.count(Summary.id)).scalar() or 0
    latest_article = db.query(func.max(Article.created_at)).scalar()

    rows = db.query(
        Summary.model_name,
        func.count(Summary.id).label('num_summaries'),
        func.avg(Summary.processing_time).label('avg_processing_time'),
        func.avg(Summary.summary_length).label('avg_summary_length'),
        func.avg(EvaluationResult.rouge_1).label('avg_rouge_1'),
        func.avg(EvaluationResult.rouge_2).label('avg_rouge_2'),
        func.avg(EvaluationResult.rouge_l).label('avg_rouge_l'),
        func.avg(EvaluationResult.bertscore_f1).label('avg_bertscore_f1')
    ).outerjoin(EvaluationResult, EvaluationResult.summary_id == Summary.id).group_by(Summary.model_name).all()

    by_model = []
    for row in rows:
        by_model.append({
            'model_name': row.model_name,
            'num_summaries': int(row.num_summaries),
            'average_processing_time': float(row.avg_processing_time) if row.avg_processing_time is not None else None,
            'average_summary_length': float(row.avg_summary_length) if row.avg_summary_length is not None else None,
            'average_rouge_1': float(row.avg_rouge_1) if row.avg_rouge_1 is not None else None,
            'average_rouge_2': float(row.avg_rouge_2) if row.avg_rouge_2 is not None else None,
            'average_rouge_l': float(row.avg_rouge_l) if row.avg_rouge_l is not None else None,
            'average_bertscore_f1': float(row.avg_bertscore_f1) if row.avg_bertscore_f1 is not None else None
        })

    return {
        'total_articles': int(total_articles),
        'total_summaries': int(total_summaries),
        'summaries_by_model': by_model,
        'latest_ingestion_time': latest_article.isoformat() if latest_article else None,
        'failed_empty_scrapes': None
    }
