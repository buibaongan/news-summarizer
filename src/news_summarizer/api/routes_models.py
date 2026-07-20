from fastapi import APIRouter, Depends
from news_summarizer.database import session as dbsession
from news_summarizer.database.models import Summary, EvaluationResult
from news_summarizer.database import repository
from sqlalchemy import func

router = APIRouter(prefix="/models", tags=["models"])

async def get_db():
    db = dbsession.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/comparison")
async def models_comparison(db=Depends(get_db)):
    q = db.query(
        Summary.model_name,
        func.count(Summary.id).label('num_summaries'),
        func.avg(Summary.processing_time).label('avg_processing_time'),
        func.avg(Summary.summary_length).label('avg_summary_length')
    ).group_by(Summary.model_name).all()

    results = []
    for row in q:
        subq = db.query(
            func.avg(EvaluationResult.rouge_1).label('avg_rouge1'),
            func.avg(EvaluationResult.rouge_2).label('avg_rouge2'),
            func.avg(EvaluationResult.rouge_l).label('avg_rougeL'),
            func.avg(EvaluationResult.bertscore_f1).label('avg_bertscore_f1')
        ).join(Summary, Summary.id == EvaluationResult.summary_id).filter(Summary.model_name == row.model_name).one()

        results.append({
            'model_name': row.model_name,
            'num_summaries': int(row.num_summaries),
            'average_processing_time': float(row.avg_processing_time) if row.avg_processing_time else None,
            'average_summary_length': float(row.avg_summary_length) if row.avg_summary_length else None,
            'average_rouge_1': float(subq.avg_rouge1) if subq.avg_rouge1 else None,
            'average_rouge_2': float(subq.avg_rouge2) if subq.avg_rouge2 else None,
            'average_rouge_l': float(subq.avg_rougeL) if subq.avg_rougeL else None,
            'average_bertscore_f1': float(subq.avg_bertscore_f1) if subq.avg_bertscore_f1 else None
        })

    return results


@router.get("/stats")
async def models_stats(db=Depends(get_db)):
    return repository.get_model_stats(db)
