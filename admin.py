"""
Admin reporting tools for the Smart POS system.

Provides:
- Reading today's transactions from the sales CSV file
- Computing summary metrics
- Displaying a simple daily sales report in the console
"""

from __future__ import annotations

import csv
from collections import Counter
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Tuple

from pos_logic import SALES_CSV_PATH


def _load_todays_transactions(csv_path: Path = SALES_CSV_PATH) -> List[Dict[str, str]]:
    """
    Load only today's transactions from the sales CSV.
    Returns a list of dictionaries for each row.
    """
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        return []

    today_str = date.today().strftime("%Y-%m-%d")
    rows: List[Dict[str, str]] = []

    with csv_path.open(mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            timestamp = row.get("DateTime", "")
            # Expecting format "YYYY-MM-DD HH:MM:SS"
            if timestamp.startswith(today_str):
                rows.append(row)

    return rows


def _parse_ordered_items(ordered_items_str: str) -> Counter:
    """
    Convert an 'OrderedItems' string like
    'Latte x2; Vada pav x1' into a Counter of item -> quantity.
    """
    counter: Counter = Counter()
    if not ordered_items_str:
        return counter

    parts = ordered_items_str.split(";")
    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Expected pattern: "<name> x<qty>"
        if " x" in part:
            name, qty_str = part.rsplit(" x", 1)
            name = name.strip()
            try:
                qty = int(qty_str.strip())
            except ValueError:
                qty = 1
        else:
            name = part
            qty = 1

        if name:
            counter[name] += qty

    return counter


def compute_daily_summary(
    rows: List[Dict[str, str]]
) -> Tuple[float, float, int, str]:
    """
    Compute:
    - total sales (final totals)
    - total GST collected
    - number of transactions
    - most sold item (by quantity)
    """
    if not rows:
        return 0.0, 0.0, 0, "N/A"

    total_sales = 0.0
    total_gst = 0.0
    item_counter: Counter = Counter()

    for row in rows:
        try:
            total_sales += float(row.get("FinalTotal", "0") or 0)
        except ValueError:
            pass
        try:
            total_gst += float(row.get("GST", "0") or 0)
        except ValueError:
            pass

        item_counter.update(_parse_ordered_items(row.get("OrderedItems", "")))

    most_sold_item = "N/A"
    if item_counter:
        most_sold_item = item_counter.most_common(1)[0][0]

    return round(total_sales, 2), round(total_gst, 2), len(rows), most_sold_item


def show_daily_report() -> None:
    """
    Read today's transactions and print a daily sales report
    to the console.
    """
    rows = _load_todays_transactions()
    total_sales, total_gst, num_tx, most_sold_item = compute_daily_summary(rows)

    print("\n==== DAILY SALES REPORT ====")
    print(f"Date: {date.today().strftime('%Y-%m-%d')}")
    print(f"Number of transactions: {num_tx}")
    print(f"Total sales (₹): {total_sales:.2f}")
    print(f"Total GST collected (₹): {total_gst:.2f}")
    print(f"Most sold item: {most_sold_item}")
    print("============================\n")


if __name__ == "__main__":
    show_daily_report()

