---
title: Phone Price Tracker
description: Scrapes iPhone, Samsung and Pixel prices from Indian e-commerce sites and shows them, sorted by price, on a live web page
ms.date: 2026-10-06
---

## Overview

This project scrapes phone prices (iPhone, Samsung Galaxy, and Google Pixel) from Indian e-commerce stores. It then:

* Serves a web page that shows live prices sorted by price in ascending order.
* Refreshes the data automatically every 2 minutes (configurable).

## Supported stores

| Store            | Method                         | Status    |
|------------------|--------------------------------|-----------|
| Amazon.in        | HTML search results            | Working   |
| Flipkart         | HTML search results            | Working   |
| Reliance Digital | Public JSON catalog endpoint   | Working   |
| Vijay Sales      | Unbxd JSON search API          | Working   |
| Poorvika         | Typesense JSON search API (in-stock items only) | Working |
| Croma            | Blocked by Akamai (HTTP 403), even in a real browser | Not added |

To add a store, subclass `BaseScraper` in `scrapers/`, implement `search()`, and
register the class in `scrapers/__init__.py`.

## Setup

```powershell
# Generated with GitHub Copilot - [Tracking ID: Hexure-Copilot]
python -m pip install -r requirements.txt
```

## Usage

Start the web app:

```powershell
# Generated with GitHub Copilot - [Tracking ID: Hexure-Copilot]
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

Open <http://localhost:8000>. A scrape starts on launch and takes about 1 to 2
minutes. The page polls the server every 5 seconds and refreshes the table when
new data arrives.

| Button               | Action                                                      |
|----------------------|-------------------------------------------------------------|
| Refresh now          | Starts a background scrape; the page updates when it ends   |

Run a single scrape without the web server (writes `output/phone_prices_latest.json`):

```powershell
# Generated with GitHub Copilot - [Tracking ID: Hexure-Copilot]
python run_scraper.py
```

Run the tests:

```powershell
# Generated with GitHub Copilot - [Tracking ID: Hexure-Copilot]
python -m pytest tests
```

On Windows you can also double-click `start.bat` to install dependencies and start the server.

## API

| Method | Path                     | Description                                         |
|--------|--------------------------|-----------------------------------------------------|
| GET    | `/api/products`          | JSON list; optional `store`, `category`, `q` filters |
| GET    | `/api/status`            | Last update time, counts per store, next run         |
| POST   | `/api/refresh`           | Start a background scrape                            |

## Configuration

Set these environment variables to override the defaults in `config.py`.

| Variable                   | Default                            | Purpose                               |
|----------------------------|------------------------------------|---------------------------------------|
| `REFRESH_INTERVAL_MINUTES` | `2`                                | Auto-refresh interval                 |
| `PAGES_PER_QUERY`          | `2`                                | Result pages scraped per search term  |
| `REQUEST_DELAY`            | `2.0`                              | Seconds between requests to one store |
| `ENABLED_STORES`           | `amazon,flipkart,reliance_digital,vijay_sales,poorvika` | Stores to scrape |
| `USE_SYSTEM_CERTS`         | `1`                                | Use the Windows certificate store (needed behind corporate proxies) |
| `MAX_SALE_DETAIL_PAGES`    | `25`                               | Flipkart sale product pages opened per run to read the bank-offer price |

## Notes and limitations

* Store layouts change often. Flipkart uses obfuscated CSS classes, so its parser
  relies on page structure. If a store returns 0 products, check the warnings on
  the web page and update that store's scraper.
* Amazon sometimes returns HTTP 503 or a captcha when it sees many requests.
  The scraper retries with backoff and keeps the last good report if every store fails.
* Third-party accessories (cases, screen guards, "compatible with" items),
  refurbished units, and AppleCare plans are filtered out.
* Check each site's terms of use before you scrape it. Keep request rates low and
  use the data for personal price comparison only.

## Sale prices

Sale columns (Sale Price, Sale Discount %, Sale Name, Status, Starts, Ends) are filled only where a store publishes them:

* **Flipkart**: listings tagged "Big Billion Days Price" (status "Upcoming" when marked "Coming Soon").
* **Vijay Sales**: scheduled offer price with start and end dates (status "Upcoming" before the start date).
* **Amazon.in**: deal badges (Great Indian Festival, Limited time deal, and similar).
* **Reliance Digital, Poorvika**: no sale price is published, so these stay blank.

Most stores reveal final sale prices only when the sale goes live, so many rows will be blank until then.

For Flipkart sale listings, the scraper also opens the product page and reads the
"Buy at ₹X" price. This is shown as **With Bank Offer**. It is the effective price
after the best card offer, so it depends on paying with that bank's card.

On the web page, use the **Sale prices only** or **Big Billion Days only** filter
to list sale rows sorted by sale price.

## Hosting online

* **Cloud (Render, Railway, Azure Container Apps, Fly.io):** push this folder to a Git repo and deploy the `Dockerfile`
  (`render.yaml` is included for Render). Set `USE_SYSTEM_CERTS=0`. Use an always-on plan, since the scheduler runs in the process.
  Stores may block datacenter IPs, so some stores can return fewer rows than from a home or office network.
* **Temporary public URL:** run `tunnel.bat` while the app is running locally. It prints a `trycloudflare.com` link.
  The link works only while this PC and the app are on.

## Hosting on GitHub Pages

The workflow in `.github/workflows/scrape.yml` scrapes every store, builds a static
copy of the page with `build_static.py`, and publishes it to GitHub Pages:

* Runs every 10 minutes (GitHub can delay scheduled runs at busy times), on every
  push to `main`, and on demand from **Actions > Scrape prices and publish > Run workflow**.
* If a run collects no products, it fails and the previous data stays online.
* The page polls the published JSON every minute and shows new data automatically.

One-time setup:

1. Make the repository public (**Settings > General > Danger Zone > Change visibility**).
2. Set **Settings > Pages > Build and deployment > Source** to **GitHub Actions**.
3. Run the workflow once from the **Actions** tab. The site is published at
   `https://<user>.github.io/<repo>/`.

To build the static site locally: `python run_scraper.py` then `python build_static.py`.
