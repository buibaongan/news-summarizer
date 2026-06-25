import os
from typing import Optional, Sequence
from ingestion import rss_collector, newsapi_collector
from scraping import article_scraper
from nlp.classifier import classify_by_keywords
from database import repository
from database import session as dbsession


DEFAULT_MODELS = ['tfidf', 'textrank', 'bart']
SUPPORTED_MODELS = {'tfidf', 'textrank', 'bart', 't5'}


def _models_from_env() -> list:
    raw = os.getenv('SUMMARY_MODELS', '')
    if not raw:
        return DEFAULT_MODELS
    return [m.strip().lower() for m in raw.split(',') if m.strip()]


def build_summarizers(models: Optional[Sequence[str]] = None) -> list:
    selected = validate_model_names(models)
    summarizers = []
    for model in selected:
        if model == 'tfidf':
            from nlp.tfidf_summarizer import TFIDFSummarizer
            summarizers.append(TFIDFSummarizer())
        elif model == 'textrank':
            from nlp.textrank_summarizer import TextRankSummarizer
            summarizers.append(TextRankSummarizer())
        elif model == 'bart':
            from nlp.transformer_summarizer import TransformerSummarizer
            summarizers.append(TransformerSummarizer(model_name='facebook/bart-large-cnn'))
        elif model == 't5':
            from nlp.transformer_summarizer import TransformerSummarizer
            summarizers.append(TransformerSummarizer(model_name='t5-small'))
    return summarizers


def validate_model_names(models: Optional[Sequence[str]] = None) -> list:
    selected = [m.lower() for m in (models or _models_from_env())]
    for model in selected:
        if model not in SUPPORTED_MODELS:
            raise ValueError(f"Unsupported summarizer model: {model}")
    return selected


def _create_missing_summaries(db, article, text: str, title: str, summarizers: Sequence, stats: dict) -> int:
    created = 0
    for summarizer in summarizers:
        from nlp.evaluator import evaluate_summary
        if repository.get_summary_by_article_and_model(db, article.id, summarizer.model_name):
            stats['skipped_existing_summaries'] += 1
            continue
        try:
            res = summarizer.summarize(text or title)
        except Exception as exc:
            stats['errors'].append({
                'url': article.url,
                'title': title,
                'model': summarizer.model_name,
                'error': f'Summarization failed: {exc}'
            })
            from nlp.tfidf_summarizer import TFIDFSummarizer
            fallback = TFIDFSummarizer().summarize(text or title)
            res = {
                'summary_text': fallback['summary_text'],
                'model_name': summarizer.model_name,
                'summary_type': f"{summarizer.summary_type}_fallback",
                'processing_time': fallback['processing_time'],
                'summary_length': fallback['summary_length']
            }
        summary = repository.create_summary(
            db,
            article_id=article.id,
            model_name=res['model_name'],
            summary_text=res['summary_text'],
            summary_type=res['summary_type'],
            processing_time=res['processing_time'],
            summary_length=res['summary_length']
        )
        if summary.id:
            stats['summaries_created'] += 1
            created += 1
        eval_res = evaluate_summary(res['summary_text'], reference=None)
        repository.create_evaluation_result(
            db,
            summary_id=summary.id,
            rouge_1=eval_res.get('rouge_1'),
            rouge_2=eval_res.get('rouge_2'),
            rouge_l=eval_res.get('rouge_l'),
            bert_p=eval_res.get('bertscore_precision'),
            bert_r=eval_res.get('bertscore_recall'),
            bert_f=eval_res.get('bertscore_f1')
        )
    return created


def ingest_all(sources_path: str = 'config/sources.json', enable_newsapi: bool = False, newsapi_key: str = '', limit: Optional[int] = None, source: Optional[str] = None, force_refresh: bool = False, models: Optional[Sequence[str]] = None, duplicate_threshold: float = 0.85) -> dict:
    db = dbsession.SessionLocal()
    stats = {'collected': 0, 'skipped_duplicates': 0, 'skipped_existing_summaries': 0, 'saved_articles': 0, 'summaries_created': 0, 'backfilled_summaries': 0, 'failed_scrapes': 0, 'errors': []}
    try:
        validate_model_names(models)
        if limit == 0:
            return stats

        articles = rss_collector.collect_from_rss(sources_path)
        if enable_newsapi and newsapi_key:
            articles += newsapi_collector.collect_from_newsapi(newsapi_key)

        # optional source filter (case-insensitive)
        if source:
            articles = [a for a in articles if a.get('source') and a.get('source').lower() == source.lower()]

        # apply limit
        if limit and isinstance(limit, int):
            articles = articles[:limit]

        stats['collected'] = len(articles)

        summarizers = build_summarizers(models)

        for a in articles:
            title = a.get('title') or ''
            url = a.get('url') or ''
            if not url:
                continue

            duplicate = repository.find_duplicate_article(db, url, title, threshold=duplicate_threshold)
            if duplicate and not force_refresh:
                art = duplicate
                full_text = art.full_text or ''
                missing_summarizers = [
                    summarizer
                    for summarizer in summarizers
                    if not repository.get_summary_by_article_and_model(db, art.id, summarizer.model_name)
                ]
                stats['skipped_existing_summaries'] += len(summarizers) - len(missing_summarizers)
                if not missing_summarizers:
                    stats['skipped_duplicates'] += 1
                    continue
                active_summarizers = missing_summarizers
            else:
                full_text, method, ok = article_scraper.scrape_article(url)
                if not ok:
                    stats['failed_scrapes'] += 1
                    stats['errors'].append({'url': url, 'title': title, 'error': f'Scraping failed using {method}'})
                    continue
                category = classify_by_keywords(title + ' ' + (full_text or ''))

                if duplicate and force_refresh:
                    repository.update_article_full_text(db, duplicate.id, full_text)
                    art = duplicate
                else:
                    art = repository.create_article(db, title=title, url=url, source=a.get('source'), published_at=a.get('published'), full_text=full_text, category=category)
                    stats['saved_articles'] += 1
                active_summarizers = summarizers

            _create_missing_summaries(db, art, full_text, title, active_summarizers, stats)

        for existing_article in repository.list_articles_for_backfill(db, source=source):
            missing_summarizers = [
                summarizer
                for summarizer in summarizers
                if not repository.get_summary_by_article_and_model(db, existing_article.id, summarizer.model_name)
            ]
            if not missing_summarizers:
                continue
            stats['backfilled_summaries'] += _create_missing_summaries(
                db,
                existing_article,
                existing_article.full_text or '',
                existing_article.title or '',
                missing_summarizers,
                stats
            )

    finally:
        db.close()

    return stats
