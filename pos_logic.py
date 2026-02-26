"""
Core business logic for the Smart POS billing system.

This module contains:
- Menu data (drinks & snacks)
- Order item model
- Price and tax calculation
- CSV-based transaction persistence

Both the CLI admin tools and the Tkinter GUI use these functions.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

# 5% GST applied on subtotal
GST_RATE = 0.05


# --- Menu definitions -------------------------------------------------------

DRINKS_MENU: Dict[str, float] = {
    "Latte": 120.0,
    "Espresso": 100.0,
    "Cappuccino": 130.0,
    "Black Coffee": 90.0,
    "Masala Tea": 60.0,
}

SNACKS_MENU: Dict[str, float] = {
    "Vada pav": 30.0,
    "Samosa": 25.0,
    "Grilled Sandwich": 70.0,
    "French Fries": 80.0,
    "Chocolate Donut": 60.0,
}


def get_all_items() -> Dict[str, float]:
    """
    Return a single dictionary with all menu items merged.
    Keys are item names, values are unit prices.
    """
    all_items: Dict[str, float] = {}
    all_items.update(DRINKS_MENU)
    all_items.update(SNACKS_MENU)
    return all_items


# --- Order model and totals -------------------------------------------------

SALES_CSV_PATH = Path("sales.csv")


@dataclass
class OrderItem:
    name: str
    quantity: int
    unit_price: float

    @property
    def line_total(self) -> float:
        return self.unit_price * self.quantity


def validate_quantity(quantity: int) -> int:
    """Ensure quantity is a positive integer."""
    if quantity <= 0:
        raise ValueError("Quantity must be a positive integer.")
    return quantity


def calculate_totals(order_items: Iterable[OrderItem]) -> Tuple[float, float, float]:
    """
    Calculate subtotal, GST amount and final total for given order items.

    Returns:
        (subtotal, gst_amount, final_total)
    """
    subtotal = sum(item.line_total for item in order_items)
    subtotal = round(subtotal, 2)
    gst_amount = round(subtotal * GST_RATE, 2)
    final_total = round(subtotal + gst_amount, 2)
    return subtotal, gst_amount, final_total


def format_order_items(order_items: Iterable[OrderItem]) -> str:
    """
    Format ordered items as: 'Latte x2; Vada pav x1'.
    """
    parts: List[str] = []
    for item in order_items:
        parts.append(f"{item.name} x{item.quantity}")
    return "; ".join(parts)


# --- CSV persistence --------------------------------------------------------

def _ensure_sales_file_has_header(csv_path: Path) -> None:
    """
    Ensure the sales CSV file exists and has a header row.
    If file does not exist or is empty, write the header.
    """
    if csv_path.exists() and csv_path.stat().st_size > 0:
        return

    with csv_path.open(mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "CustomerName",
                "OrderedItems",
                "Subtotal",
                "GST",
                "FinalTotal",
                "PaymentMethod",
                "DateTime",
            ]
        )


def save_transaction(
    customer_name: str,
    order_items: Iterable[OrderItem],
    payment_method: str,
    csv_path: Path | None = None,
) -> Tuple[float, float, float]:
    """
    Persist a single transaction to the sales CSV file.

    Returns:
        (subtotal, gst_amount, final_total) for the transaction.
    """
    if not customer_name.strip():
        raise ValueError("Customer name cannot be empty.")

    items_list = list(order_items)
    if not items_list:
        raise ValueError("Order must contain at least one item.")

    subtotal, gst_amount, final_total = calculate_totals(items_list)
    ordered_items_str = format_order_items(items_list)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if csv_path is None:
        csv_path = SALES_CSV_PATH

    _ensure_sales_file_has_header(csv_path)

    with csv_path.open(mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                customer_name.strip(),
                ordered_items_str,
                f"{subtotal:.2f}",
                f"{gst_amount:.2f}",
                f"{final_total:.2f}",
                payment_method.strip(),
                timestamp,
            ]
        )

    return subtotal, gst_amount, final_total

