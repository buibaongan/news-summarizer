from fastapi import APIRouter, Depends, Query
from database import session as dbsession
from database.models import Article
from sqlalchemy import or_

router = APIRouter(prefix="/search", tags=["search"])

async def get_db():
    db = dbsession.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("")
async def search(q: str = Query(...), limit: int = 20, db=Depends(get_db)):
    # naive search in title and full_text
    res = db.query(Article).filter(or_(Article.title.ilike(f"%{q}%"), Article.full_text.ilike(f"%{q}%"))).limit(limit).all()
    return res
