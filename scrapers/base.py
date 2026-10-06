# Generated with GitHub Copilot - [Tracking ID: Hexure-Copilot]
"""Shared scraper infrastructure: HTTP session, retries, price parsing, data model."""
from __future__ import annotations

import logging
import random
import re
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Iterable

import requests

import config
from core.filters import categorize, is_target_phone

log = logging.getLogger(__name__)

if config.USE_SYSTEM_CERTS:
    try:
        import truststore

        truststore.inject_into_ssl()
    except ImportError:  # pragma: no cover
        log.warning("truststore not installed; falling back to certifi bundle")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36 Edg/128.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
]

_PRICE_RE = re.compile(r"[\d,]+(?:\.\d+)?")


def parse_price(text: str | None) -> float | None:
    """Convert strings like 'â‚¹1,43,990.00' to 143990.0."""
    if not text:
        return None
    m = _PRICE_RE.search(text.replace("\u00a0", " "))
    if not m:
        return None
    try:
        value = float(m.group(0).replace(",", ""))
    except ValueError:
        return None
    return value if value > 0 else None


@dataclass
class Product:
    name: str
    price: float
    store: str
    category: str
    url: str
    mrp: float | None = None
    product_id: str = ""
    sale_price: float | None = None
    sale_name: str = ""
    sale_status: str = ""  # "Live", "Upcoming" or ""
    sale_starts: str = ""
    sale_ends: str = ""
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    @property
    def discount_pct(self) -> float | None:
        if self.mrp and self.mrp > self.price:
            return round((self.mrp - self.price) / self.mrp * 100, 1)
        return None

    @property
    def sale_discount_pct(self) -> float | None:
        if self.sale_price and self.price > self.sale_price:
            return round((self.price - self.sale_price) / self.price * 100, 1)
        return None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["discount_pct"] = self.discount_pct
        d["sale_discount_pct"] = self.sale_discount_pct
        return d


class BaseScraper(ABC):
    name: str = "base"
    display_name: str = "Base"
    base_url: str = ""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": random.choice(USER_AGENTS),
                "Accept-Language": "en-IN,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7",
            }
        )
        self.errors: list[str] = []

    def fetch(self, url: str, **kwargs) -> requests.Response | None:
        for attempt in range(1, config.MAX_RETRIES + 2):
            try:
                resp = self.session.get(url, timeout=config.REQUEST_TIMEOUT, **kwargs)
                if resp.status_code == 200:
                    return resp
                log.warning("%s: HTTP %s for %s (attempt %d)", self.name, resp.status_code, url, attempt)
                if resp.status_code in (403, 404):
                    break
            except requests.RequestException as exc:
                log.warning("%s: %s for %s (attempt %d)", self.name, exc, url, attempt)
            time.sleep(config.REQUEST_DELAY * attempt + random.random())
            self.session.headers["User-Agent"] = random.choice(USER_AGENTS)
        self.errors.append(f"Failed to fetch {url}")
        return None

    def polite_pause(self) -> None:
        time.sleep(config.REQUEST_DELAY + random.random())

    @abstractmethod
    def search(self, query: str, category: str, page: int) -> Iterable[Product]:
        """Yield products for one result page."""

    def scrape(self, queries: dict[str, str], pages: int) -> list[Product]:
        results: dict[str, Product] = {}
        for category, query in queries.items():
            for page in range(1, pages + 1):
                try:
                    found = list(self.search(query, category, page))
                except Exception as exc:  # keep other queries running if a layout changes
                    log.exception("%s: error parsing '%s' page %d", self.name, query, page)
                    self.errors.append(f"{query} p{page}: {exc}")
                    found = []
                for p in found:
                    if not is_target_phone(p.name):
                        continue
                    p.category = categorize(p.name, p.category)
                    if p.sale_price and p.sale_price >= p.price and p.sale_status != "Upcoming":
                        p.sale_price = p.price
                    key = p.product_id or p.url
                    if key not in results or p.price < results[key].price:
                        results[key] = p
                self.polite_pause()
                if not found:
                    break
        log.info("%s: collected %d products", self.name, len(results))
        return list(results.values())

    def scrape_with_errors(self, queries: dict[str, str], pages: int) -> tuple[list[Product], list[str]]:
        return self.scrape(queries, pages), self.errors

