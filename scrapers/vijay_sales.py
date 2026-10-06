# Generated with GitHub Copilot - [Tracking ID: Hexure-Copilot]
from __future__ import annotations

from datetime import datetime
from typing import Iterable
from urllib.parse import quote

from core.filters import normalize_name
from scrapers.base import BaseScraper, Product


class VijaySalesScraper(BaseScraper):
    """Uses the Unbxd search API behind vijaysales.com (the site itself renders client-side)."""

    name = "vijay_sales"
    display_name = "Vijay Sales"
    base_url = "https://www.vijaysales.com"
    api_url = "https://mdm.vijaysales.com/web/api/search/unbxd-search/v1"
    rows = 30

    def search(self, query: str, category: str, page: int) -> Iterable[Product]:
        # The API expects paging parameters encoded inside the "q" value.
        q = quote(f"{query}&page={page}&rows={self.rows}", safe="")
        resp = self.fetch(
            f"{self.api_url}?q={q}&fq=",
            headers={"Accept": "application/json", "Origin": self.base_url, "Referer": f"{self.base_url}/"},
        )
        if not resp:
            return
        try:
            products = resp.json()["response"]["products"]
        except (ValueError, KeyError):
            self.errors.append(f"Unexpected response for '{query}'")
            return
        for item in products:
            brand = item.get("brand") or []
            brand = brand[0] if isinstance(brand, list) and brand else brand
            if str(brand).lower() not in ("apple", "samsung"):
                continue
            if str(item.get("cityId_1_status_unx_ts", "Available")).lower() != "available":
                continue
            price = item.get("cityId_1_sellingPrice_unx_d") or item.get("vsp") or item.get("price")
            title, url = item.get("title"), item.get("productUrl")
            if not (price and title and url):
                continue
            mrp = item.get("mrp")
            sale_price = None
            sale_status = sale_starts = sale_ends = ""
            offer = item.get("cityId_1_offerPrice_unx_d") or item.get("offerPrice")
            has_window = item.get("cityId_1_offerPriceStartDatetime_unx_ts") or item.get("cityId_1_offerPriceEndDatetime_unx_ts")
            if offer and has_window and "available" in str(item.get("cityId_1_offerAvailable_unx_ts", "")).lower():
                sale_starts = str(item.get("cityId_1_offerPriceStartDatetime_unx_ts", ""))
                sale_ends = str(item.get("cityId_1_offerPriceEndDatetime_unx_ts") or item.get("offerPriceEndDatetime") or "")
                sale_status = "Live"
                try:
                    if sale_starts and datetime.fromisoformat(sale_starts) > datetime.now():
                        sale_status = "Upcoming"
                        price = item.get("cityId_1_price_unx_d") or price
                except ValueError:
                    pass
                sale_price = float(offer)
            yield Product(
                name=normalize_name(title),
                price=float(price),
                mrp=float(mrp) if mrp else None,
                store=self.display_name,
                category=category,
                url=url,
                sale_price=sale_price or None,
                sale_name="Vijay Sales offer price" if sale_price else "",
                sale_status=sale_status,
                sale_starts=sale_starts,
                sale_ends=sale_ends,
                product_id=f"vijay:{item.get('uniqueId') or item.get('sku') or url}",
            )

