# Generated with GitHub Copilot - [Tracking ID: Hexure-Copilot]
"""Web app: view latest phone prices and download the Excel report.

Run:  python -m uvicorn app:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

import config
from core.service import service

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
templates = Jinja2Templates(directory=str(config.BASE_DIR / "templates"))
scheduler = BackgroundScheduler(daemon=True)


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler.add_job(
        service.run, "interval", minutes=config.REFRESH_INTERVAL_MINUTES,
        id="refresh", next_run_time=datetime.now(), max_instances=1, coalesce=True,
    )
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="Phone Price Tracker", lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request, "index.html", {"interval": config.REFRESH_INTERVAL_MINUTES}
    )


@app.get("/api/status")
def status():
    data = service.status()
    job = scheduler.get_job("refresh")
    data["next_run"] = job.next_run_time.isoformat(timespec="seconds") if job and job.next_run_time else None
    return data


@app.get("/api/products")
def products(store: str | None = None, category: str | None = None, q: str | None = None):
    items = service.load_latest().get("products", [])
    if store:
        items = [p for p in items if p["store"].lower() == store.lower()]
    if category:
        items = [p for p in items if p["category"].lower() == category.lower()]
    if q:
        items = [p for p in items if q.lower() in p["name"].lower()]
    return {"count": len(items), "products": items}


@app.post("/api/refresh", status_code=202)
def refresh():
    started = service.trigger_async()
    return {"started": started, "message": "Refresh started" if started else "Refresh already running"}


@app.get("/download")
async def download(fresh: bool = False):
    """Download the latest Excel. With ?fresh=true a new scrape is run first."""
    if fresh:
        if service.running:
            while service.running:
                await asyncio.sleep(2)
        else:
            await run_in_threadpool(service.run)
    if not config.LATEST_EXCEL.exists():
        raise HTTPException(status_code=404, detail="Report not generated yet. Try again in a few minutes.")
    stamp = datetime.fromtimestamp(config.LATEST_EXCEL.stat().st_mtime)
    return FileResponse(
        config.LATEST_EXCEL,
        filename=f"phone_prices_{stamp:%Y%m%d_%H%M}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Cache-Control": "no-store"},
    )
