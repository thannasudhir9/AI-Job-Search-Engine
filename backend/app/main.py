from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS
from .db import SessionLocal, init_db
from .routers import applications, jobs, matches, profile, resumes, system, tailor


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    from .services.scheduler import start_scheduler

    scheduler = start_scheduler()

    # first-run convenience: seed a few well-known public boards + initial sync
    def _seed_and_sync():
        from .models import Company
        from .services.sync import sync_all

        db = SessionLocal()
        try:
            seeds = [
                ("Stripe", "greenhouse", "stripe"),
                ("Airbnb", "greenhouse", "airbnb"),
                ("Dropbox", "greenhouse", "dropbox"),
            ]
            import sqlalchemy as sa

            for name, source, slug in seeds:
                exists = (
                    db.query(Company)
                    .filter(Company.source == source, Company.slug == slug)
                    .first()
                )
                if not exists and db.query(Company).count() == 0:
                    db.add(Company(name=name, source=source, slug=slug))
            db.commit()
            has_jobs = db.execute(sa.text("SELECT COUNT(*) FROM job")).scalar()
            if has_jobs == 0:
                sync_all(db)
        finally:
            db.close()

    try:
        import threading

        threading.Thread(target=_seed_and_sync, daemon=True).start()
    except Exception:
        pass

    yield

    from .services.scheduler import stop_scheduler

    stop_scheduler()


app = FastAPI(title="Local Job Agent", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (system, profile, resumes, jobs, matches, tailor, applications):
    app.include_router(module.router, prefix="/api")


@app.get("/")
def root():
    return {"name": "Local Job Agent API", "docs": "/docs"}
