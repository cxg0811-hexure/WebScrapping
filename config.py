# Generated with GitHub Copilot - [Tracking ID: Hexure-Copilot]
"""Central configuration. Values can be overridden with environment variables."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", BASE_DIR / "output"))
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

# Comma separated list to enable a subset, e.g. "amazon,flipkart".
ENABLED_STORES = [s.strip().lower() for s in os.getenv("ENABLED_STORES", "amazon,flipkart,reliance_digital,vijay_sales,poorvika").split(",") if s.strip()]

# Optional file of products scraped from another network (home PC), merged for stores that return nothing.
_local_file = os.getenv("LOCAL_STORES_FILE", str(BASE_DIR / "data" / "local_stores.json"))
LOCAL_STORES_FILE = Path(_local_file) if _local_file else None  # empty string disables merging
LOCAL_STORES_MAX_AGE_MIN = int(os.getenv("LOCAL_STORES_MAX_AGE_MIN", "180"))

# Optional Indian HTTP(S) proxy, e.g. http://user:pass@host:port. Only the stores in PROXY_STORES use it
# (the ones that block datacenter IPs), which keeps proxy bandwidth low.
PROXY_URL = os.getenv("PROXY_URL", "").strip()
PROXY_STORES = [s.strip().lower() for s in os.getenv("PROXY_STORES", "amazon,reliance_digital").split(",") if s.strip()]

# Use the OS certificate store (needed behind corporate TLS-inspecting proxies).
USE_SYSTEM_CERTS = os.getenv("USE_SYSTEM_CERTS", "1") == "1"

