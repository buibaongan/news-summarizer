import os
import requests
from database.session import SessionLocal
from database.repository import get_unsent_summaries, mark_summary_sent

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_message(text: str):
    if not TOKEN or not CHAT_ID:
        return False
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    payload = {'chat_id': CHAT_ID, 'text': text}
    r = requests.post(url, json=payload, timeout=10)
    return r.ok

def deliver_unsent():
    db = SessionLocal()
    try:
        from database.models import Summary
        summaries = db.query(Summary).filter(Summary.sent_to_telegram == False).all()
        for s in summaries:
            text = f"{s.model_name} summary:\n{s.summary_text[:1000]}"
            ok = send_message(text)
            if ok:
                s.sent_to_telegram = True
        db.commit()
    finally:
        db.close()
