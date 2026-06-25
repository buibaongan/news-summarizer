from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import session as dbsession
from database.models import Base, EvaluationResult
from scripts import run_evaluation


class FakeSummarizer:
    model_name = 'fake'
    summary_type = 'extractive'

    def summarize(self, text):
        return {
            'summary_text': 'short summary',
            'model_name': self.model_name,
            'summary_type': self.summary_type,
            'processing_time': 0.01,
            'summary_length': 2
        }


def setup_in_memory_db():
    engine = create_engine('sqlite:///:memory:', connect_args={"check_same_thread": False}, poolclass=StaticPool)
    dbsession.engine = engine
    dbsession.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(engine)


def test_load_evaluation_dataset(tmp_path):
    dataset = tmp_path / 'eval.jsonl'
    dataset.write_text('{"id":"one","article":"article text","reference_summary":"reference"}\n')

    records = run_evaluation.load_evaluation_dataset(str(dataset))

    assert records[0]['id'] == 'one'
    assert records[0]['reference_summary'] == 'reference'


def test_run_evaluation_stores_metrics(monkeypatch, tmp_path):
    setup_in_memory_db()
    dataset = tmp_path / 'eval.jsonl'
    dataset.write_text('{"id":"one","article":"article text","reference_summary":"reference"}\n')
    monkeypatch.setattr(run_evaluation, 'build_summarizers', lambda models=None: [FakeSummarizer()])
    monkeypatch.setattr(run_evaluation, 'evaluate_summary', lambda summary, reference: {
        'rouge_1': 0.5,
        'rouge_2': 0.25,
        'rouge_l': 0.45,
        'bertscore_precision': 0.6,
        'bertscore_recall': 0.55,
        'bertscore_f1': 0.57
    })

    stats = run_evaluation.run_evaluation(str(dataset), models=['fake'])

    assert stats['total_articles'] == 1
    assert stats['total_summaries'] == 1
    db = dbsession.SessionLocal()
    metric = db.query(EvaluationResult).first()
    assert metric.rouge_1 == 0.5
    assert metric.bertscore_f1 == 0.57
    db.close()
