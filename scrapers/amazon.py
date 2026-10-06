# Generated with GitHub Copilot - [Tracking ID: Hexure-Copilot]
from __future__ import annotations

import re
from typing import Iterable
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from core.filters import normalize_name
from scrapers.base import BaseScraper, Product, parse_price

_BRANDS = {"apple", "samsung"}
_DEAL_RE = re.compile(r"(great indian festival|limited time deal|deal of the day|lightning deal|prime day|blockbuster deal)", re.I)


class AmazonScraper(BaseScraper):
    name = "amazon"
    display_name = "Amazon.in"
    base_url = "https://www.amazon.in"

    def search(self, query: str, category: str, page: int) -> Iterable[Product]:
        url = f"{self.base_url}/s?k={quote_plus(query)}&page={page}"
        resp = self.fetch(url)
        if not resp:
            return
        if "api-services-support@amazon.com" in resp.text or "/errors/validateCaptcha" in resp.text:
            self.errors.append(f"Captcha served for '{query}' page {page}")
            return
        soup = BeautifulSoup(resp.text, "lxml")
        for item in soup.select('div[data-component-type="s-search-result"]'):
            asin = item.get("data-asin", "")
            title_el = item.select_one('[data-cy="title-recipe"]') or item.select_one("h2")
            price_el = item.select_one("span.a-price:not(.a-text-price) span.a-offscreen")
            if not (asin and title_el and price_el):
                continue
            title = title_el.get_text(" ", strip=True)
            headings = [h.get_text(" ", strip=True) for h in item.select("h2")]
            # Brand is shown as its own heading above the title on most results.
            brand = headings[0].lower() if len(headings) > 1 else ""
            if brand in _BRANDS and not title.lower().startswith(brand):
                title = f"{brand.title()} {title}"
            elif title.lower().startswith("iphone"):
                title = f"Apple {title}"
            price = parse_price(price_el.get_text())
            if not price:
                continue
            deal = _DEAL_RE.search(item.get_text(" ", strip=True))
            mrp_el = item.select_one("span.a-price.a-text-price span.a-offscreen")
            yield Product(
                name=normalize_name(title),
                price=price,
                mrp=parse_price(mrp_el.get_text()) if mrp_el else None,
                store=self.display_name,
                category=category,
                url=f"{self.base_url}/dp/{asin}",
                product_id=f"amazon:{asin}",
                sale_price=price if deal else None,
                sale_name=deal.group(1).title() if deal else "",
                sale_status="Live" if deal else "",
            )

