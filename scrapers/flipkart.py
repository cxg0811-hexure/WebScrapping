# Generated with GitHub Copilot - [Tracking ID: Hexure-Copilot]
from __future__ import annotations

import re
from typing import Iterable
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

import config
from core.filters import normalize_name
from scrapers.base import BaseScraper, Product, parse_price

# Flipkart uses obfuscated CSS classes that change often, so parsing is structural.
_OFFER_WORDS = re.compile(r"exchange|bank|cashback|\bemi\b|upto|up to", re.IGNORECASE)


class FlipkartScraper(BaseScraper):
    name = "flipkart"
    display_name = "Flipkart"
    base_url = "https://www.flipkart.com"

    def search(self, query: str, category: str, page: int) -> Iterable[Product]:
        url = f"{self.base_url}/search?q={quote_plus(query)}&page={page}"
        resp = self.fetch(url)
        if not resp:
            return
        soup = BeautifulSoup(resp.text, "lxml")
        for card in soup.select("div[data-id]"):
            pid = card.get("data-id", "")
            link = card.select_one('a[href*="/p/"]')
            title = None
            titled = card.select_one("a[title]")
            if titled:
                title = titled["title"]
            if not title:
                img = card.select_one("img[alt]")
                title = img["alt"] if img else None
            if not (pid and link and title):
                continue

            prices: list[float] = []
            seen = set()
            # The currency symbol and amount can be split across text nodes, so read the element text.
            for node in card.find_all(string=lambda t: t and "\u20b9" in t):
                el = node.parent
                if el is None or id(el) in seen:
                    continue
                seen.add(id(el))
                context = el.parent.get_text(" ", strip=True) if el.parent else ""
                if _OFFER_WORDS.search(context):
                    continue
                value = parse_price(el.get_text(" ", strip=True))
                if value:
                    prices.append(value)
            if not prices:
                continue

            price = prices[0]
            card_text = card.get_text(" ", strip=True)
            sale_name = "Big Billion Days" if "big billion days price" in card_text.lower() else ""
            upcoming = "coming soon" in card_text.lower()
            mrp = next((p for p in prices[1:] if p > price), None)
            href = link["href"].split("&")[0]
            yield Product(
                name=normalize_name(title),
                price=price,
                mrp=mrp,
                store=self.display_name,
                category=category,
                url=href if href.startswith("http") else f"{self.base_url}{href}",
                product_id=f"flipkart:{pid}",
                sale_price=price if sale_name else None,
                sale_name=sale_name,
                sale_status=("Upcoming" if upcoming else "Live") if sale_name else "",
            )

    def enrich(self, products: list[Product]) -> None:
        """Read the 'Buy at ₹X' bank-offer price from the product page of each sale listing."""
        sale_items = [p for p in products if p.sale_name][: config.MAX_SALE_DETAIL_PAGES]
        for p in sale_items:
            resp = self.fetch(p.url)
            if resp:
                p.offer_price = parse_offer_price(resp.text, p.price)
            self.polite_pause()


_BUY_AT = re.compile(r"^\s*Buy at\s*\u20b9\s*([\d,]+)", re.IGNORECASE)


def parse_offer_price(html: str, price: float) -> float | None:
    """Return the first 'Buy at ₹X' value on a product page if it is a plausible discount on price."""
    for text in BeautifulSoup(html, "lxml").find_all(string=_BUY_AT):
        value = parse_price(_BUY_AT.match(text).group(1))
        if value and price * 0.5 <= value < price:
            return value
        break
    return None

