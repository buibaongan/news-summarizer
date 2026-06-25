from fastapi import APIRouter, Depends, HTTPException
from database import session as dbsession
from database import repository
from typing import List
from datetime import datetime

router = APIRouter(prefix="/articles", tags=["articles"])

async def get_db():
    db = dbsession.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("")
async def list_articles(limit: int = 50, db=Depends(get_db)):
    return repository.list_articles(db, limit=limit)


@router.get("/{article_id}")
async def get_article(article_id: int, db=Depends(get_db)):
    a = repository.get_article(db, article_id)
    if not a:
        raise HTTPException(status_code=404, detail="Article not found")
    summaries_by_model = {}
    for summary in sorted(a.summaries, key=lambda item: item.created_at or datetime.min, reverse=True):
        summaries_by_model.setdefault(summary.model_name, summary)
    return {
        "id": a.id,
        "title": a.title,
        "url": a.url,
        "source": a.source,
        "published_at": a.published_at,
        "full_text": a.full_text,
        "category": a.category,
        "created_at": a.created_at,
        "summaries": [
            {
                "id": summary.id,
                "model_name": summary.model_name,
                "summary_text": summary.summary_text,
                "summary_type": summary.summary_type,
                "processing_time": summary.processing_time,
                "summary_length": summary.summary_length,
                "created_at": summary.created_at,
                "sent_to_telegram": summary.sent_to_telegram
            }
            for summary in summaries_by_model.values()
        ]
    }
