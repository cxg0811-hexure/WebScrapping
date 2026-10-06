# Generated with GitHub Copilot - [Tracking ID: Hexure-Copilot]
"""Central configuration. Values can be overridden with environment variables."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", BASE_DIR / "output"))
HISTORY_DIR = OUTPUT_DIR / "history"
LATEST_EXCEL = OUTPUT_DIR / "phone_prices_latest.xlsx"
LATEST_JSON = OUTPUT_DIR / "phone_prices_latest.json"

# Search terms sent to every store; each term maps to a product category.
SEARCH_QUERIES = {
    "iPhone": "apple iphone",
    "Samsung": "samsung galaxy smartphone",
    "Google Pixel": "google pixel smartphone",
}
BRAND_BY_CATEGORY = {"iPhone": "Apple", "Samsung": "Samsung", "Google Pixel": "Google"}

PAGES_PER_QUERY = int(os.getenv("PAGES_PER_QUERY", "2"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "25"))
# Polite delay (seconds) between requests to the same store.
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "1.0"))
# Max product pages opened per run to read the bank-offer ("Buy at") price of sale listings.
MAX_SALE_DETAIL_PAGES = int(os.getenv("MAX_SALE_DETAIL_PAGES", "25"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))

# Background refresh interval for the web app.
REFRESH_INTERVAL_MINUTES = int(os.getenv("REFRESH_INTERVAL_MINUTES", "2"))
HISTORY_KEEP = int(os.getenv("HISTORY_KEEP", "10"))

# Comma separated list to enable a subset, e.g. "amazon,flipkart".
ENABLED_STORES = [s.strip().lower() for s in os.getenv("ENABLED_STORES", "amazon,flipkart,reliance_digital,vijay_sales,poorvika").split(",") if s.strip()]

# Use the OS certificate store (needed behind corporate TLS-inspecting proxies).
USE_SYSTEM_CERTS = os.getenv("USE_SYSTEM_CERTS", "1") == "1"

