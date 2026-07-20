import os
from news_summarizer.app import scheduler
from news_summarizer.delivery import telegram_bot
from unittest.mock import patch


def test_scheduler_job_calls_ingest_and_telegram(monkeypatch):
    # mock ingest_all to be quick
    monkeypatch.setattr('news_summarizer.ingestion.ingest_pipeline.ingest_all', lambda *args, **kwargs: {'collected': 0})
    sent = {'ok': False}

    def fake_deliver():
        sent['ok'] = True

    monkeypatch.setattr(telegram_bot, 'deliver_unsent', fake_deliver)
    monkeypatch.setattr(scheduler.settings, 'enable_telegram', True)

    # run job directly
    scheduler._job()
    assert sent['ok'] is True
