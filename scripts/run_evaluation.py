import argparse
import json
from pathlib import Path
from typing import Sequence

from database import repository
from database import session as dbsession
from ingestion.ingest_pipeline import build_summarizers
from nlp.evaluator import evaluate_summary


def load_evaluation_dataset(path: str) -> list:
    records = []
    with Path(path).open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if not record.get('article') or not record.get('reference_summary'):
                raise ValueError('Each evaluation record needs article and reference_summary fields')
            records.append(record)
    return records


def run_evaluation(dataset_path: str, models: Sequence[str] = None) -> dict:
    dbsession.Base.metadata.create_all(dbsession.engine)
    records = load_evaluation_dataset(dataset_path)
    summarizers = build_summarizers(models)
    db = dbsession.SessionLocal()
    try:
        for record in records:
            article_id = record.get('id') or record.get('title') or 'evaluation'
            url = f"evaluation://{article_id}"
            article = repository.get_article_by_url(db, url)
            if not article:
                article = repository.create_article(
                    db,
                    title=record.get('title') or article_id,
                    url=url,
                    source='evaluation',
                    full_text=record['article'],
                    category='evaluation'
                )

            for summarizer in summarizers:
                result = summarizer.summarize(record['article'])
                summary = repository.create_summary(
                    db,
                    article_id=article.id,
                    model_name=result['model_name'],
                    summary_text=result['summary_text'],
                    summary_type=result['summary_type'],
                    processing_time=result['processing_time'],
                    summary_length=result['summary_length']
                )
                metrics = evaluate_summary(result['summary_text'], record['reference_summary'])
                repository.create_evaluation_result(
                    db,
                    summary_id=summary.id,
                    rouge_1=metrics.get('rouge_1'),
                    rouge_2=metrics.get('rouge_2'),
                    rouge_l=metrics.get('rouge_l'),
                    bert_p=metrics.get('bertscore_precision'),
                    bert_r=metrics.get('bertscore_recall'),
                    bert_f=metrics.get('bertscore_f1')
                )

        return repository.get_model_stats(db)
    finally:
        db.close()


def print_model_table(stats: dict):
    print('model | summaries | avg time | avg length | rouge-1 | rouge-2 | rouge-l | bert-f1')
    print('--- | ---: | ---: | ---: | ---: | ---: | ---: | ---:')
    for row in stats['summaries_by_model']:
        print(
            f"{row['model_name']} | {row['num_summaries']} | "
            f"{row['average_processing_time']} | {row['average_summary_length']} | "
            f"{row['average_rouge_1']} | {row['average_rouge_2']} | "
            f"{row['average_rouge_l']} | {row['average_bertscore_f1']}"
        )


def main():
    parser = argparse.ArgumentParser(description='Run summarizer evaluation on a JSONL dataset.')
    parser.add_argument('--dataset', default='data/evaluation/sample.jsonl')
    parser.add_argument('--models', default='tfidf,textrank,bart')
    args = parser.parse_args()
    models = [model.strip() for model in args.models.split(',') if model.strip()]
    stats = run_evaluation(args.dataset, models=models)
    print_model_table(stats)


if __name__ == '__main__':
    main()
