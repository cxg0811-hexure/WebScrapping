# Generated with GitHub Copilot - [Tracking ID: Hexure-Copilot]
"""Runs all store scrapers in parallel and publishes the latest Excel/JSON."""
from __future__ import annotations

import json
import logging
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import config
from core.excel import build_workbook
from scrapers import SCRAPERS

log = logging.getLogger(__name__)


class ScrapeService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.running = False
        self.started_at: datetime | None = None
        self.last_error: str | None = None

    def status(self) -> dict:
        data = self.load_latest()
        return {
            "running": self.running,
            "started_at": self.started_at.isoformat(timespec="seconds") if self.started_at else None,
            "last_updated": data.get("generated_at"),
            "total": len(data.get("products", [])),
            "stores": data.get("stores", {}),
            "excel_available": config.LATEST_EXCEL.exists(),
            "last_error": self.last_error,
        }

    @staticmethod
    def load_latest() -> dict:
        if config.LATEST_JSON.exists():
            try:
                return json.loads(config.LATEST_JSON.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                log.exception("Could not read %s", config.LATEST_JSON)
        return {}

    def trigger_async(self) -> bool:
        """Start a scrape in the background. Returns False if one is already running."""
        if self.running:
            return False
        threading.Thread(target=self.run, daemon=True, name="scrape-run").start()
        return True

    def run(self) -> dict | None:
        if not self._lock.acquire(blocking=False):
            log.info("Scrape already in progress; skipping")
            return None
        self.running, self.started_at, self.last_error = True, datetime.now(), None
        try:
            return self._run()
        except Exception as exc:
            log.exception("Scrape failed")
            self.last_error = str(exc)
            return None
        finally:
            self.running = False
            self._lock.release()

    def _run(self) -> dict:
        enabled = {k: v for k, v in SCRAPERS.items() if k in config.ENABLED_STORES}
        products, stores = [], {}
        with ThreadPoolExecutor(max_workers=len(enabled) or 1) as pool:
            futures = {
                pool.submit(cls().scrape_with_errors, config.SEARCH_QUERIES, config.PAGES_PER_QUERY): cls
                for cls in enabled.values()
            }
            for fut in as_completed(futures):
                cls = futures[fut]
                try:
                    items, errors = fut.result()
                except Exception as exc:
                    items, errors = [], [str(exc)]
                products.extend(p.to_dict() for p in items)
                stores[cls.display_name] = {"count": len(items), "errors": errors[:10]}

        generated_at = datetime.now()
        if not products:
            previous = self.load_latest()
            if previous.get("products"):
                # Keep the last good file rather than overwriting it with an empty report.
                self.last_error = "No products scraped this run; kept previous report."
                log.warning(self.last_error)
                return previous

        products.sort(key=lambda p: (p["price"], p["name"]))
        payload = {"generated_at": generated_at.isoformat(timespec="seconds"), "stores": stores, "products": products}

        build_workbook(products, config.LATEST_EXCEL, generated_at)
        tmp_json = config.LATEST_JSON.with_suffix(".json.tmp")
        tmp_json.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp_json.replace(config.LATEST_JSON)
        self._archive(generated_at)
        log.info("Published %d products to %s", len(products), config.LATEST_EXCEL)
        return payload

    @staticmethod
    def _archive(generated_at: datetime) -> None:
        config.HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(config.LATEST_EXCEL, config.HISTORY_DIR / f"phone_prices_{generated_at:%Y%m%d_%H%M%S}.xlsx")
        for old in sorted(config.HISTORY_DIR.glob("phone_prices_*.xlsx"))[: -config.HISTORY_KEEP]:
            old.unlink(missing_ok=True)


service = ScrapeService()
