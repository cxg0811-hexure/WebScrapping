# Generated with GitHub Copilot - [Tracking ID: Hexure-Copilot]
from __future__ import annotations

import time
from typing import Iterable

import config
from core.filters import normalize_name
from scrapers.base import BaseScraper, Product


class PoorvikaScraper(BaseScraper):
    """Queries the Typesense search endpoint that powers poorvika.com."""

    name = "poorvika"
    display_name = "Poorvika"
    base_url = "https://www.poorvika.com"
    api_url = "https://proxy.poorvika.com/typesense"

    def search(self, query: str, category: str, page: int) -> Iterable[Product]:
        body = {
            "searches": [{
                "collection": "productsnew",
                "q": {"iPhone": "iphone", "Samsung": "galaxy"}.get(category, query),
                "num_typos": 1,
                "query_by": "name,categories,item_code,sku",
                "query_by_weights": "4,3,2,1",
                "sort_by": "_text_match:desc",
                "page": page,
                "per_page": 50,
                "filter_by": "sellable:=1 && variant_status:=1 && special_price:>-1 "
                             f"&& stock_status:=In Stock && brand_name:={config.BRAND_BY_CATEGORY.get(category, 'Apple')}",
            }]
        }
        data = None
        for attempt in range(1, config.MAX_RETRIES + 2):
            try:
                resp = self.session.post(
                    self.api_url, json=body, timeout=config.REQUEST_TIMEOUT,
                    headers={"Referer": f"{self.base_url}/", "Origin": self.base_url},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    break
            except (ValueError, OSError):
                pass
            time.sleep(config.REQUEST_DELAY * attempt)
        if data is None:
            self.errors.append(f"Failed to query '{query}'")
            return
        for hit in data["results"][0].get("hits", []):
            doc = hit["document"]
            price = doc.get("special_price") or doc.get("selling_price") or doc.get("price")
            name, slug = doc.get("name"), doc.get("slug")
            if not (price and name and slug):
                continue
            mrp = None
            try:
                mrp = doc["mrp"][0]["price"][0]["price"]
            except (KeyError, IndexError, TypeError):
                pass
            yield Product(
                name=normalize_name(name),
                price=float(price),
                mrp=float(mrp) if mrp else None,
                store=self.display_name,
                category=category,
                url=f"{self.base_url}/{slug}/p",
                product_id=f"poorvika:{doc.get('id') or slug}",
            )


