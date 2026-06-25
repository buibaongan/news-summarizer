import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.config import settings
from ingestion import ingest_pipeline
from delivery import telegram_bot

logger = logging.getLogger(__name__)
scheduler = None

def _job():
    logger.info('Scheduled ingest job starting')
    try:
        stats = ingest_pipeline.ingest_all(sources_path='config/sources.json', enable_newsapi=settings.enable_newsapi, newsapi_key=settings.newsapi_key)
        logger.info(f'Ingest stats: {stats}')
        # after ingest, attempt Telegram delivery if enabled
        if settings.enable_telegram:
            telegram_bot.deliver_unsent()
    except Exception as e:
        logger.exception('Scheduled ingest failed')

def start():
    global scheduler
    if scheduler:
        return
    if not settings.enable_scheduler:
        logger.info('Scheduler disabled by settings')
        return
    scheduler = BackgroundScheduler()
    interval = int(settings.ingest_interval_minutes or 120)
    scheduler.add_job(_job, IntervalTrigger(minutes=interval), id='ingest_job', replace_existing=True)
    scheduler.start()
    logger.info(f'Scheduler started, interval={interval} minutes')

def shutdown():
    global scheduler
    if scheduler:
        scheduler.shutdown()
        scheduler = None
