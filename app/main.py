from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from database import session as dbsession
from api import routes_articles, routes_summarize, routes_search, routes_ingest, routes_models, routes_sources
from ingestion import scheduler as ingest_scheduler

app = FastAPI(title="News Summarizer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include routers
app.include_router(routes_articles.router)
app.include_router(routes_summarize.router)
app.include_router(routes_search.router)
app.include_router(routes_ingest.router)
app.include_router(routes_models.router)
app.include_router(routes_sources.router)


@app.on_event("startup")
def startup_event():
    # create tables
    dbsession.Base.metadata.create_all(dbsession.engine)
    # start scheduler if enabled
    try:
        ingest_scheduler.start()
    except Exception:
        pass


@app.get("/health")
async def health():
    return {"status": "ok"}
