from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from news_summarizer.ingestion.ingest_pipeline import build_summarizers

router = APIRouter(prefix="/summarize", tags=["summarize"])

class SummarizeRequest(BaseModel):
    text: str
    model: str = 'bart'


@router.post("")
async def summarize(req: SummarizeRequest):
    model_aliases = {
        'facebook/bart-large-cnn': 'bart',
        't5-small': 't5'
    }
    requested_model = model_aliases.get(req.model, req.model)
    try:
        summarizers = build_summarizers([requested_model])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    s = summarizers[0]
    return s.summarize(req.text)
