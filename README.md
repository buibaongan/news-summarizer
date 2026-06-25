News Summarizer
================

Automatic news summarization project with a FastAPI backend, RSS/NewsAPI ingestion, scraping, multiple summarizers, SQLAlchemy persistence, scheduled delivery, evaluation tooling, and a React dashboard.

Backend quick start
-------------------

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://localhost:8000/health
```

How to demo this project
------------------------

Use lightweight summarizers for demos unless you have already downloaded transformer models:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
DATABASE_URL=sqlite:///./data/demo.db SUMMARY_MODELS=tfidf uvicorn app.main:app --reload
```

In another terminal, start the dashboard:

```bash
cd frontend
npm install
VITE_API_BASE=http://localhost:8000 npm run dev
```

Open `http://localhost:5173`.

Quick API smoke checks:

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"limit":0,"models":["tfidf"]}'
curl http://localhost:8000/articles
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{"text":"First sentence. Second sentence.","model":"tfidf"}'
curl "http://localhost:8000/search?q=sentence"
curl http://localhost:8000/models/comparison
curl http://localhost:8000/models/stats
```

`limit: 0` is useful for verifying the ingest endpoint without making live RSS or scraping requests. For a full demo with real articles, remove the limit or set it to a small number and use `models:["tfidf"]` first.

SQLite local mode
-----------------

SQLite is the default database for local development.

```env
DATABASE_URL=sqlite:///./news.db
```

Docker also defaults to SQLite and stores the database under `./data`:

```bash
docker compose up --build app
```

PostgreSQL Docker mode
----------------------

PostgreSQL is optional. Start the Postgres profile and point the backend at the service:

```bash
DATABASE_URL=postgresql+psycopg2://postgres:postgres@postgres:5432/news_summarizer \
docker compose --profile postgres up --build app postgres
```

Optional Postgres environment variables:

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `POSTGRES_PORT`

API
---

- `GET /health`
- `GET /articles?limit=50`
- `GET /articles/{id}`
- `GET /search?q=keyword`
- `GET /models/comparison`
- `GET /models/stats`
- `POST /summarize`
- `POST /ingest`

`POST /ingest` accepts:

```json
{
  "limit": 10,
  "source": "BBC",
  "force_refresh": false,
  "models": ["tfidf", "textrank", "bart", "t5"]
}
```

Smart deduplication
-------------------

Ingestion now checks for duplicates by:

- exact URL
- normalized title
- title similarity threshold

If a duplicate is found and `force_refresh=false`, the article is skipped. If `force_refresh=true`, the existing article is updated and re-summarized.

Summarizers
-----------

Available model keys for ingestion:

- `tfidf`
- `textrank`
- `bart`
- `t5`

Default models are controlled by:

```env
SUMMARY_MODELS=tfidf,textrank,bart
```

T5 uses `t5-small` by default. Tests mock Hugging Face pipelines so model downloads are not required during pytest.

Transformer model cache
-----------------------

BART and T5 are Hugging Face transformer models. The first ingest that uses them may be slow because the container has to download model files and load them on CPU. T5 is much smaller than BART.

Docker Compose mounts `./models` into the backend container and configures Hugging Face cache paths:

```env
HF_HOME=/app/models/huggingface
HF_HUB_CACHE=/app/models/huggingface/hub
TRANSFORMERS_CACHE=/app/models/huggingface/transformers
```

This means downloaded models are kept in your local `./models/huggingface` folder and should survive:

```bash
docker compose down
docker compose --profile frontend up
```

For quick demos, use only `tfidf`. Add `t5` or `bart` after the app is working and you are ready for the first model download.

React dashboard
---------------

The dashboard lives in `frontend/` and uses React with Vite.

```bash
cd frontend
npm install
npm run dev
```

The frontend defaults to `http://localhost:8000` for the API. Override it with:

```env
VITE_API_BASE=http://localhost:8000
```

Docker profile:

```bash
docker compose --profile frontend up --build app frontend
```

Dashboard pages:

- latest articles
- article detail with full text and summaries
- search
- model comparison
- ingest controls
- monitoring/statistics

Evaluation dataset
------------------

Evaluation samples live under `data/evaluation/`. JSONL format:

```json
{"id":"sample-1","article":"long article text","reference_summary":"human-written summary"}
```

Run the evaluation script:

```bash
python scripts/run_evaluation.py --dataset data/evaluation/sample.jsonl --models tfidf,textrank,bart
```

The script stores generated summaries and ROUGE/BERTScore metrics in the database, then prints a model comparison table.

Monitoring/statistics
---------------------

`GET /models/stats` returns:

- total articles
- total summaries
- summaries by model
- average processing time by model
- average summary length by model
- average ROUGE/BERTScore by model where available
- latest ingestion time
- failed/empty scrape count placeholder

Scheduler and Telegram
----------------------

Environment variables:

- `ENABLE_SCHEDULER=true`
- `INGEST_INTERVAL_MINUTES=120`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

When enabled, the scheduler runs ingestion periodically and attempts Telegram delivery for unsent summaries.

Tests
-----

```bash
pytest -q
```

CI runs pytest on GitHub Actions. Transformer pipelines are mocked in tests to keep CI fast and offline-friendly.
