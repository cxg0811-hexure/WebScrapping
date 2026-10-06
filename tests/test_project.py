# Generated with GitHub Copilot - [Tracking ID: Hexure-Copilot]
import json
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
import config
from core.filters import categorize, is_target_phone, normalize_name
from scrapers.base import Product, parse_price
from scrapers.flipkart import FlipkartScraper, parse_offer_price
from scrapers.poorvika import PoorvikaScraper
from scrapers.reliance_digital import RelianceDigitalScraper
from scrapers.vijay_sales import VijaySalesScraper


class FakeResponse:
    status_code = 200

    def __init__(self, payload=None, text=""):
        self._payload, self.text = payload, text

    def json(self):
        return self._payload


@pytest.mark.parametrize("text,expected", [
    ("₹1,43,990", 143990.0), ("₹ 25,499.50", 25499.5), ("free", None), (None, None), ("₹0", None),
])
def test_parse_price(text, expected):
    assert parse_price(text) == expected


@pytest.mark.parametrize("title,ok", [
    ("Apple iPhone 17 256GB", True),
    ("Samsung Galaxy S25 Ultra 5G (256GB)", True),
    ("Google Pixel 9 Pro (128GB)", True),
    ("Samsung Galaxy Watch 7", False),
    ("Google Pixel Buds Pro", False),
    ("Samsung Galaxy Tab S9", False),
    ("Apple iPhone 16 Silicone Case with MagSafe", False),
    ("Spigen Tempered Glass for iPhone 16", False),
    ("Apple iPhone 15 Refurbished", False),
    ("Apple iPhone Air MagSafe Battery", False),
])
def test_genuine_filter(title, ok):
    assert is_target_phone(title) is ok


def test_categorize_and_normalize():
    assert categorize("Samsung Galaxy S25", "x") == "Samsung"
    assert categorize("Google Pixel 9", "x") == "Google Pixel"
    assert categorize("Apple iPhone 17", "x") == "iPhone"
    assert normalize_name("Apple iPhone Air\u200b: 13-inch with M3 chip") == "Apple iPhone Air"


def test_reliance_parser(monkeypatch):
    payload = {"items": [
        {"name": "Apple iPhone 18 Pro", "slug": "apple-18", "uid": 1, "sellable": True,
         "brand": {"name": "Apple"}, "price": {"effective": {"min": 150000}, "marked": {"min": 160000}}},
        {"name": "OnePlus Phone", "slug": "s", "brand": {"name": "OnePlus"}, "price": {"effective": {"min": 1}}},
    ]}
    s = RelianceDigitalScraper()
    monkeypatch.setattr(s, "fetch", lambda *a, **k: FakeResponse(payload))
    items = list(s.search("apple iphone", "iPhone", 1))
    assert len(items) == 1 and items[0].price == 150000 and items[0].discount_pct == 6.2


def test_vijay_parser(monkeypatch):
    payload = {"response": {"products": [
        {"brand": ["Apple"], "title": "Apple iPhone 17", "productUrl": "https://x/p/1", "uniqueId": "1",
         "cityId_1_sellingPrice_unx_d": 80000, "mrp": 82000, "cityId_1_status_unx_ts": "Available"},
        {"brand": ["Apple"], "title": "Apple iPhone 16", "productUrl": "https://x/p/2", "uniqueId": "2",
         "price": 70000, "cityId_1_status_unx_ts": "Out of Stock"},
    ]}}
    s = VijaySalesScraper()
    monkeypatch.setattr(s, "fetch", lambda *a, **k: FakeResponse(payload))
    items = list(s.search("apple iphone", "iPhone", 1))
    assert [p.price for p in items] == [80000.0]


def test_poorvika_parser(monkeypatch):
    doc = {"name": "Apple iPhone 17 ( Black, 256GB )", "slug": "apple-iphone-17", "id": "a",
           "special_price": 99900, "mrp": [{"price": [{"price": 109900}]}]}
    payload = {"results": [{"hits": [{"document": doc}]}]}
    s = PoorvikaScraper()
    monkeypatch.setattr(s.session, "post", lambda *a, **k: FakeResponse(payload))
    item = next(iter(s.search("apple iphone", "iPhone", 1)))
    assert item.url.endswith("/apple-iphone-17/p") and item.mrp == 109900.0


def test_flipkart_skips_exchange_offer(monkeypatch):
    html = """<div data-id="X1"><a href="/apple-iphone-16/p/itm?pid=X1" title="Apple iPhone 16 (Black, 128 GB)">
    <div><div>₹69,900</div><div><div>₹ 79,900</div></div></div>
    <div>Upto <span>₹47,000</span> Off on Exchange</div></a></div>"""
    s = FlipkartScraper()
    monkeypatch.setattr(s, "fetch", lambda *a, **k: FakeResponse(text=html))
    item = next(iter(s.search("apple iphone", "iPhone", 1)))
    assert item.price == 69900 and item.mrp == 79900


def test_scrape_dedupes_and_filters(monkeypatch):
    s = RelianceDigitalScraper()
    mk = lambda n, p: Product(name=n, price=p, store="S", category="iPhone", url="u", product_id="id1")
    monkeypatch.setattr(s, "search", lambda q, c, pg: [mk("Apple iPhone 17", 90), mk("Apple iPhone 17", 80),
                                                       Product("Apple iPhone Case", 5, "S", "x", "u2", product_id="c")] if pg == 1 else [])
    monkeypatch.setattr(s, "polite_pause", lambda: None)
    out = s.scrape({"iPhone": "apple iphone"}, 2)
    assert len(out) == 1 and out[0].price == 80


def test_proxy_only_for_listed_stores(monkeypatch):
    monkeypatch.setattr(config, "PROXY_URL", "http://u:p@proxy.in:8000")
    assert FlipkartScraper().session.proxies == {}
    from scrapers.amazon import AmazonScraper
    assert AmazonScraper().session.proxies["https"] == "http://u:p@proxy.in:8000"
    monkeypatch.setattr(config, "PROXY_URL", "")
    assert AmazonScraper().session.proxies == {}


def test_flipkart_offer_price_parser():
    html = "<div>Big Billion Days Price</div><div>\u20b947,999</div><div>Buy at \u20b943,999</div><div>Buy at \u20b91,000</div>"
    assert parse_offer_price(html, 47999) == 43999
    assert parse_offer_price("<div>Buy at \u20b91,000</div>", 47999) is None  # implausibly low
    assert parse_offer_price("<div>no offer</div>", 47999) is None


def test_flipkart_enrich_fetches_only_sale_items(monkeypatch):
    s = FlipkartScraper()
    calls = []
    monkeypatch.setattr(s, "fetch", lambda url, **k: calls.append(url) or FakeResponse(text="<p>Buy at \u20b990</p>"))
    monkeypatch.setattr(s, "polite_pause", lambda: None)
    sale = Product("Google Pixel 10a", 100, "Flipkart", "Google Pixel", "http://sale", sale_price=100, sale_name="Big Billion Days")
    plain = Product("Google Pixel 9", 100, "Flipkart", "Google Pixel", "http://plain")
    s.enrich([sale, plain])
    assert calls == ["http://sale"] and sale.offer_price == 90 and plain.offer_price is None


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "LATEST_JSON", tmp_path / "latest.json")
    import app as app_module
    return TestClient(app_module.app)


def test_download_route_removed(client):
    assert client.get("/download").status_code == 404
    assert "Download" not in client.get("/").text


def test_api_products_and_status(client):
    rows = [Product("Apple iPhone 17", 90000, "A", "iPhone", "http://a").to_dict()]
    config.LATEST_JSON.write_text(json.dumps({"generated_at": "2026-01-01T00:00:00", "stores": {}, "products": rows}))
    assert client.get("/api/products", params={"q": "iphone"}).json()["count"] == 1
    assert client.get("/api/products", params={"store": "zzz"}).json()["count"] == 0
    assert client.get("/api/status").json()["total"] == 1


def test_service_writes_json_only(tmp_path, monkeypatch):
    from core.service import ScrapeService

    class Fake:
        display_name = "Fake"
        def scrape_with_errors(self, queries, pages):
            return [Product("Google Pixel 9", 50, "Fake", "Google Pixel", "u"),
                    Product("Apple iPhone 17", 10, "Fake", "iPhone", "u")], []

    monkeypatch.setattr(config, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(config, "LATEST_JSON", tmp_path / "latest.json")
    monkeypatch.setattr(config, "LOCAL_STORES_FILE", None)
    monkeypatch.setattr(config, "ENABLED_STORES", ["fake"])
    monkeypatch.setattr("core.service.SCRAPERS", {"fake": Fake})
    out = ScrapeService().run()
    assert [p["price"] for p in out["products"]] == [10, 50]
    assert [f.name for f in tmp_path.iterdir()] == ["latest.json"]


def test_merge_local_fills_only_empty_fresh_stores(tmp_path, monkeypatch):
    from core.service import ScrapeService
    f = tmp_path / "local.json"
    amazon = Product("Apple iPhone 17", 90, "Amazon.in", "iPhone", "u").to_dict()
    flip = Product("Apple iPhone 17", 80, "Flipkart", "iPhone", "u").to_dict()
    def write(ts):
        f.write_text(json.dumps({"generated_at": ts, "stores": {"Amazon.in": {"count": 1, "errors": []}, "Flipkart": {"count": 1, "errors": []}},
                                 "products": [amazon, flip]}))
    monkeypatch.setattr(config, "LOCAL_STORES_FILE", f)
    write(datetime.now().isoformat())
    products, stores = [], {"Amazon.in": {"count": 0, "errors": []}, "Flipkart": {"count": 5, "errors": []}}
    ScrapeService._merge_local(products, stores)
    assert [p["store"] for p in products] == ["Amazon.in"] and stores["Amazon.in"]["count"] == 1
    write("2020-01-01T00:00:00")
    products = []
    ScrapeService._merge_local(products, {"Amazon.in": {"count": 0, "errors": []}})
    assert products == []


def test_sale_discount():
    p = Product("Samsung Galaxy S25", 80000, "S", "Samsung", "u", sale_price=60000, sale_name="BBD")
    assert p.sale_discount_pct == 25.0
    assert Product("x", 5, "S", "c", "u").sale_discount_pct is None


def test_flipkart_sale_tag(monkeypatch):
    html = """<div data-id="X2"><a href="/s/p/itm?pid=X2" title="Samsung Galaxy A36 5G (128 GB)">x</a>
    <div>Coming Soon</div><div>₹30,999</div><div>₹38,999</div><div>Big Billion Days Price</div></div>"""
    s = FlipkartScraper()
    monkeypatch.setattr(s, "fetch", lambda *a, **k: FakeResponse(text=html))
    item = next(iter(s.search("samsung galaxy", "Samsung", 1)))
    assert item.sale_price == 30999.0 and item.sale_status == "Upcoming" and "Big Billion" in item.sale_name
