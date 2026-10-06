# Generated with GitHub Copilot - [Tracking ID: Hexure-Copilot]
from __future__ import annotations

from typing import Iterable
from urllib.parse import quote_plus

from core.filters import normalize_name
from scrapers.base import BaseScraper, Product


class RelianceDigitalScraper(BaseScraper):
    """Uses the public JSON catalog endpoint that powers reliancedigital.in search."""

    name = "reliance_digital"
    display_name = "Reliance Digital"
    base_url = "https://www.reliancedigital.in"

    def search(self, query: str, category: str, page: int) -> Iterable[Product]:
        url = (
            f"{self.base_url}/ext/raven-api/catalog/v1.0/products"
            f"?q={quote_plus(query)}&page_size=24&page_no={page}&page_type=number"
        )
        resp = self.fetch(url, headers={"Accept": "application/json"})
        if not resp:
            return
        try:
            data = resp.json()
        except ValueError:
            self.errors.append(f"Non-JSON response for '{query}'")
            return
        for item in data.get("items", []):
            brand = (item.get("brand") or {}).get("name", "")
            if brand.lower() not in ("apple", "samsung") or not item.get("sellable", True):
                continue
            price_info = item.get("price") or {}
            price = (price_info.get("effective") or {}).get("min")
            mrp = (price_info.get("marked") or {}).get("min")
            name, slug = item.get("name"), item.get("slug")
            if not (name and slug and price):
                continue
            yield Product(
                name=normalize_name(name),
                price=float(price),
                mrp=float(mrp) if mrp else None,
                store=self.display_name,
                category=category,
                url=f"{self.base_url}/product/{slug}",
                product_id=f"reliance:{item.get('uid') or slug}",
            )

