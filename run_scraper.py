# Generated with GitHub Copilot - [Tracking ID: Hexure-Copilot]
"""Run a single scrape from the command line (no web server).

Usage:  python run_scraper.py
"""
import logging
import sys

import config
from core.service import service

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    result = service.run()
    if not result or not result.get("products"):
        print(f"Scrape failed: {service.last_error}")
        sys.exit(1)
    for store, info in result["stores"].items():
        print(f"{store:<18} {info['count']:>4} products  errors={len(info['errors'])}")
    print(f"Total: {len(result['products'])} -> {config.LATEST_JSON}")
