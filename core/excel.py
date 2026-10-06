# Generated with GitHub Copilot - [Tracking ID: Hexure-Copilot]
"""Build the formatted Excel workbook (sorted by price, ascending)."""
from __future__ import annotations

import os
import tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

HEADER_FILL = PatternFill("solid", fgColor="1F1F1F")
HEADER_FONT = Font(bold=True, color="FFFFFF")
INR_FORMAT = '"₹"#,##,##0'

COLUMNS = [
    ("#", 6), ("Product", 70), ("Category", 14), ("Store", 16), ("Price (?)", 14),
    ("MRP (?)", 14), ("Discount %", 11), ("Sale Price (?)", 15), ("Sale Discount %", 12),
    ("Sale Name", 24), ("Sale Status", 11), ("Sale Starts", 18), ("Sale Ends", 18),
    ("Link", 12), ("Scraped At", 20),
]
LINK_COL, SCRAPED_COL = 14, 15


def _write_header(ws, columns):
    for idx, (title, width) in enumerate(columns, start=1):
        cell = ws.cell(row=1, column=idx, value=title)
        cell.fill, cell.font = HEADER_FILL, HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.column_dimensions[get_column_letter(idx)].width = width
    ws.freeze_panes = "A2"


def build_workbook(products: list[dict], path: Path, generated_at: datetime) -> Path:
    rows = sorted(products, key=lambda p: (p["price"], p["name"]))
    wb = Workbook()

    ws = wb.active
    ws.title = "All Phones"
    _write_header(ws, COLUMNS)
    for i, p in enumerate(rows, start=1):
        r = i + 1
        ws.cell(r, 1, i)
        ws.cell(r, 2, p["name"])
        ws.cell(r, 3, p["category"])
        ws.cell(r, 4, p["store"])
        ws.cell(r, 5, p["price"]).number_format = INR_FORMAT
        if p.get("mrp") and p["mrp"] > p["price"]:
            ws.cell(r, 6, p["mrp"]).number_format = INR_FORMAT
        if p.get("discount_pct") is not None:
            ws.cell(r, 7, p["discount_pct"] / 100).number_format = "0.0%"
        if p.get("sale_price"):
            ws.cell(r, 8, p["sale_price"]).number_format = INR_FORMAT
        if p.get("sale_discount_pct") is not None:
            ws.cell(r, 9, p["sale_discount_pct"] / 100).number_format = "0.0%"
        ws.cell(r, 10, p.get("sale_name", ""))
        ws.cell(r, 11, p.get("sale_status", ""))
        ws.cell(r, 12, p.get("sale_starts", ""))
        ws.cell(r, 13, p.get("sale_ends", ""))
        link = ws.cell(r, LINK_COL, "Open")
        link.hyperlink, link.style = p["url"], "Hyperlink"
        ws.cell(r, SCRAPED_COL, p["scraped_at"].replace("T", " "))
    if rows:
        ws.auto_filter.ref = f"A1:{get_column_letter(len(COLUMNS))}{len(rows) + 1}"

    # One sheet per category, also sorted ascending by price.
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for p in rows:
        by_cat[p["category"]].append(p)
    cat_cols = [("Product", 70), ("Store", 16), ("Price (₹)", 14), ("MRP (₹)", 14), ("Link", 12)]
    for cat in sorted(by_cat):
        cws = wb.create_sheet(cat[:31])
        _write_header(cws, cat_cols)
        for r, p in enumerate(by_cat[cat], start=2):
            cws.cell(r, 1, p["name"])
            cws.cell(r, 2, p["store"])
            cws.cell(r, 3, p["price"]).number_format = INR_FORMAT
            if p.get("mrp") and p["mrp"] > p["price"]:
                cws.cell(r, 4, p["mrp"]).number_format = INR_FORMAT
            if p.get("sale_price"):
                cws.cell(r, 5, p["sale_price"]).number_format = INR_FORMAT
            cws.cell(r, 6, p.get("sale_name", ""))
            c = cws.cell(r, 7, "Open")
            c.hyperlink, c.style = p["url"], "Hyperlink"

    summary = wb.create_sheet("Summary", 0)
    summary["A1"] = "Phone Price Report (iPhone, Samsung, Google Pixel)"
    summary["A1"].font = Font(bold=True, size=14)
    summary["A2"] = f"Generated: {generated_at:%Y-%m-%d %H:%M:%S}"
    summary["A3"] = f"Total listings: {len(rows)}"
    _hdr = [("Category", 18), ("Listings", 10), ("Lowest Price (₹)", 18), ("Cheapest Product", 70), ("Store", 16)]
    for idx, (title, width) in enumerate(_hdr, start=1):
        cell = summary.cell(5, idx, title)
        cell.fill, cell.font = HEADER_FILL, HEADER_FONT
        summary.column_dimensions[get_column_letter(idx)].width = width
    for r, cat in enumerate(sorted(by_cat, key=lambda c: by_cat[c][0]["price"]), start=6):
        cheapest = by_cat[cat][0]
        summary.cell(r, 1, cat)
        summary.cell(r, 2, len(by_cat[cat]))
        summary.cell(r, 3, cheapest["price"]).number_format = INR_FORMAT
        summary.cell(r, 4, cheapest["name"])
        summary.cell(r, 5, cheapest["store"])

    # Write atomically so a download never receives a half-written file.
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(suffix=".xlsx", dir=path.parent)
    os.close(fd)
    try:
        wb.save(tmp)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return path
