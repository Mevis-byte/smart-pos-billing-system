"""
Simple CLI interface for the Smart POS system.

This is primarily here to demonstrate the separation between:
- Menu display and order-taking logic
- Core billing / persistence logic (`billing_core`)

The GUI version should be used for normal operation.
"""

from __future__ import annotations

from typing import List

from billing_core import OrderItem, save_transaction, validate_quantity
from menus import DRINKS_MENU, SNACKS_MENU


PAYMENT_METHODS = ("Cash", "Card", "UPI")


def show_menu() -> None:
    """Print drinks and snacks menu to the console."""
    print("\n--- DRINKS MENU ---")
    for name, price in DRINKS_MENU.items():
        print(f"{name:15} : ₹{price:.2f}")

    print("\n--- SNACKS MENU ---")
    for name, price in SNACKS_MENU.items():
        print(f"{name:15} : ₹{price:.2f}")


def _prompt_item_name() -> str:
    all_items = {**DRINKS_MENU, **SNACKS_MENU}
    while True:
        name = input("Enter item name (or 'done' to finish): ").strip()
        if name.lower() == "done":
            return ""
        if name in all_items:
            return name
        print("Invalid item name. Please choose from the menu.")


def _prompt_quantity() -> int:
    while True:
        qty_str = input("Enter quantity: ").strip()
        if not qty_str.isdigit():
            print("Quantity must be a whole number.")
            continue
        qty = int(qty_str)
        try:
            return validate_quantity(qty)
        except ValueError as exc:
            print(exc)


def take_order_from_cli() -> List[OrderItem]:
    """Interactively build an order from user input."""
    all_items = {**DRINKS_MENU, **SNACKS_MENU}
    order_items: List[OrderItem] = []

    while True:
        item_name = _prompt_item_name()
        if not item_name:
            break
        quantity = _prompt_quantity()
        unit_price = all_items[item_name]
        order_items.append(OrderItem(name=item_name, quantity=quantity, unit_price=unit_price))
        print(f"Added {item_name} x{quantity} to order.")

    return order_items


def _prompt_payment_method() -> str:
    print("\nPayment methods:")
    for idx, method in enumerate(PAYMENT_METHODS, start=1):
        print(f"{idx}. {method}")
    while True:
        choice = input("Choose payment method (1-3): ").strip()
        if choice in {"1", "2", "3"}:
            return PAYMENT_METHODS[int(choice) - 1]
        print("Invalid choice. Please enter 1, 2, or 3.")


def run_cli_billing_flow() -> None:
    """
    End-to-end billing flow for CLI usage:
    - Show menu
    - Take order
    - Ask for payment method
    - Save transaction
    """
    print("==== SMART POS (CLI MODE) ====")
    customer_name = input("Enter customer name: ").strip()
    if not customer_name:
        print("Customer name is required. Exiting.")
        return

    show_menu()
    order_items = take_order_from_cli()
    if not order_items:
        print("No items in order. Exiting.")
        return

    payment_method = _prompt_payment_method()
    subtotal, gst_amount, final_total = save_transaction(
        customer_name=customer_name,
        order_items=order_items,
        payment_method=payment_method,
    )

    print("\n--- BILL SUMMARY ---")
    print(f"Customer: {customer_name}")
    print(f"Subtotal: ₹{subtotal:.2f}")
    print(f"GST (5%): ₹{gst_amount:.2f}")
    print(f"Final Total: ₹{final_total:.2f}")
    print(f"Payment Method: {payment_method}")
    print("Transaction saved to sales.csv")


if __name__ == "__main__":
    run_cli_billing_flow()

