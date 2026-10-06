# Generated with GitHub Copilot - [Tracking ID: Hexure-Copilot]
"""Scraper registry. To add a store, subclass BaseScraper and register it here."""
from scrapers.amazon import AmazonScraper
from scrapers.flipkart import FlipkartScraper
from scrapers.poorvika import PoorvikaScraper
from scrapers.reliance_digital import RelianceDigitalScraper
from scrapers.vijay_sales import VijaySalesScraper

SCRAPERS = {
    cls.name: cls
    for cls in (AmazonScraper, FlipkartScraper, RelianceDigitalScraper, VijaySalesScraper, PoorvikaScraper)
}
