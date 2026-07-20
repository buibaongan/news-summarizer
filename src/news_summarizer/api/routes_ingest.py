from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from news_summarizer.app.config import settings
from news_summarizer.ingestion.ingest_pipeline import ingest_all

router = APIRouter(prefix="", tags=["ingest"])


class IngestRequest(BaseModel):
    limit: Optional[int] = None
    source: Optional[str] = None
    force_refresh: bool = False
    models: Optional[List[str]] = None


@router.post("/ingest")
async def ingest(req: Optional[IngestRequest] = Body(default=None)):
    req = req or IngestRequest()
    try:
        stats = ingest_all(sources_path='config/sources.json', enable_newsapi=settings.enable_newsapi, newsapi_key=settings.newsapi_key, limit=req.limit, source=req.source, force_refresh=req.force_refresh, models=req.models)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return stats
