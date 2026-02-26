from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import tkinter as tk
from tkinter import messagebox, ttk


# =============================================================================
# 1. ORIGINAL COFFEE BOT (CONSOLE)
# =============================================================================


def print_welcome() -> None:
    print("☕ Hello, welcome to my coffee shop! ☕")


def ask_name() -> str:
    name = input("May I please know your name? ")
    if not name.strip():
        name = "Guest"
    print(f"Hello {name}, welcome to my coffee shop!!!")
    return name


def show_menu(title: str, items: Dict[str, Tuple[str, float]]) -> None:
    print("\n" + title)
    print("-" * len(title))
    for code, (item_name, price) in items.items():
        print(f"{code}. {item_name} - ₹{price}")


def choose_items(menu_dict: Dict[str, Tuple[str, float]], category_name: str):
    order: List[Tuple[str, float, int]] = []
    while True:
        show_menu(f"{category_name} menu", menu_dict)
        choice = input(
            "\nEnter the number of what you want to order "
            f"in {category_name.lower()} (or press Enter to stop): "
        ).strip()

        if choice == "":
            break

        if choice not in menu_dict:
            print("Oops, that's not on the menu. Please choose a valid number.")
            continue

        qty_str = input("How many would you like? ").strip()
        if not qty_str.isdigit() or int(qty_str) <= 0:
            print("Please enter a valid positive number for quantity.")
            continue

        qty = int(qty_str)
        name, price = menu_dict[choice]
        order.append((name, price, qty))
        print(f"Added {qty} x {name} to your order!")

        more = input("Would you like to add more from this menu? (yes/no) ").strip().lower()
        if more not in ("yes", "y"):
            break

    return order


def print_bill(name: str, drinks, snacks) -> None:
    print("\n================= BILL =================")
    print(f"Customer: {name}")

    total = 0

    if drinks:
        print("\nDrinks:")
        for item_name, price, qty in drinks:
            line_total = price * qty
            total += line_total
            print(f"- {item_name} x {qty} = ₹{line_total}")

    if snacks:
        print("\nSnacks:")
        for item_name, price, qty in snacks:
            line_total = price * qty
            total += line_total
            print(f"- {item_name} x {qty} = ₹{line_total}")

    print("\n----------------------------------------")
    print(f"Total: ₹{total}")

    payment_method = input("How would you like to pay? (cash/card/upi) ").strip().lower()
    if payment_method not in ("cash", "card", "upi"):
        payment_method = "cash"
    print(f"Payment method: {payment_method.upper()}")

    print("Thank you for visiting our coffee shop! Have a great day! ☕")
    print("========================================\n")


def coffeebot_cli_main() -> None:
    drinks_menu = {
        "1": ("Latte", 120),
        "2": ("Black coffee", 90),
        "3": ("Cappuccino", 130),
        "4": ("Cold coffee", 140),
        "5": ("Diet coke", 60),
        "6": ("Plain water", 20),
    }

    snacks_menu = {
        "1": ("Vada pav", 40),
        "2": ("Misal pav", 80),
        "3": ("Lays chips", 30),
        "4": ("Biscuits", 25),
        "5": ("Cheese sandwich", 90),
    }

    print_welcome()
    name = ask_name()

    choice = input("Would you like to order anything? (yes/no) ").strip().lower()
    if choice not in ("yes", "y"):
        print("Ok, you can order next time!!!")
        return

    print("Ok then, here is our menu!!")

    drinks_order = choose_items(drinks_menu, "Drinks")

    snack_choice = input(
        "While your drinks are being prepared, would you like to order some snacks? (yes/no) "
    ).strip().lower()

    snacks_order = []
    if snack_choice in ("yes", "y"):
        snacks_order = choose_items(snacks_menu, "Snacks")

    if not drinks_order and not snacks_order:
        print("You didn't order anything in the end. Maybe next time!")
        return

    print_bill(name, drinks_order, snacks_order)


# =============================================================================
# 2. SMART POS CORE LOGIC (MENUS, BILLING, CSV PERSISTENCE)
# =============================================================================

# 5% GST
GST_RATE = 0.05

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
    """Return a combined dict of all menu items."""
    all_items: Dict[str, float] = {}
    all_items.update(DRINKS_MENU)
    all_items.update(SNACKS_MENU)
    return all_items


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
    """Format ordered items as: 'Latte x2; Vada pav x1'."""
    parts: List[str] = []
    for item in order_items:
        parts.append(f"{item.name} x{item.quantity}")
    return "; ".join(parts)


def _ensure_sales_file_has_header(csv_path: Path) -> None:
    """Ensure the sales CSV exists and has a header row."""
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
    Returns (subtotal, gst_amount, final_total).
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


# =============================================================================
# 3. ADMIN REPORTING (DAILY SALES)
# =============================================================================


def _load_todays_transactions(csv_path: Path = SALES_CSV_PATH) -> List[Dict[str, str]]:
    """Load only today's transactions from the sales CSV."""
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        return []

    today_str = date.today().strftime("%Y-%m-%d")
    rows: List[Dict[str, str]] = []

    with csv_path.open(mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            timestamp = row.get("DateTime", "")
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
    rows: List[Dict[str, str]],
) -> Tuple[float, float, int, str]:
    """
    Compute:
    - total sales
    - total GST collected
    - number of transactions
    - most sold item
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
    """Print a daily sales report for today's transactions."""
    rows = _load_todays_transactions()
    total_sales, total_gst, num_tx, most_sold_item = compute_daily_summary(rows)

    print("\n==== DAILY SALES REPORT ====")
    print(f"Date: {date.today().strftime('%Y-%m-%d')}")
    print(f"Number of transactions: {num_tx}")
    print(f"Total sales (₹): {total_sales:.2f}")
    print(f"Total GST collected (₹): {total_gst:.2f}")
    print(f"Most sold item: {most_sold_item}")
    print("============================\n")


# =============================================================================
# 4. TKINTER GUI FOR SMART POS
# =============================================================================

PAYMENT_METHODS = ("Cash", "Card", "UPI")


class PosGUI:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Smart POS - Billing System")
        self.root.geometry("800x500")

        self.order_items: List[OrderItem] = []
        self.all_items = get_all_items()

        self.customer_name_var = tk.StringVar()
        self.quantity_var = tk.StringVar(value="1")
        self.selected_item_var = tk.StringVar(value="")
        self.payment_method_var = tk.StringVar(value=PAYMENT_METHODS[0])
        self.subtotal_var = tk.StringVar(value="0.00")
        self.gst_var = tk.StringVar(value="0.00")
        self.total_var = tk.StringVar(value="0.00")

        self._build_layout()

    def _build_layout(self) -> None:
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill="x")

        ttk.Label(top_frame, text="Customer Name:").pack(side="left")
        ttk.Entry(top_frame, textvariable=self.customer_name_var, width=30).pack(
            side="left", padx=5
        )

        center_frame = ttk.Frame(self.root, padding=10)
        center_frame.pack(fill="both", expand=True)

        menu_frame = ttk.Frame(center_frame)
        menu_frame.pack(side="left", fill="y", padx=(0, 10))

        order_frame = ttk.Frame(center_frame)
        order_frame.pack(side="right", fill="both", expand=True)

        drinks_label = ttk.Label(menu_frame, text="Drinks", font=("Segoe UI", 10, "bold"))
        drinks_label.pack(anchor="w")

        drinks_buttons_frame = ttk.Frame(menu_frame)
        drinks_buttons_frame.pack(anchor="w", pady=(0, 10))

        for name, price in DRINKS_MENU.items():
            ttk.Button(
                drinks_buttons_frame,
                text=f"{name} (₹{price:.0f})",
                command=lambda n=name: self._on_item_selected(n),
            ).pack(fill="x", pady=1)

        snacks_label = ttk.Label(menu_frame, text="Snacks", font=("Segoe UI", 10, "bold"))
        snacks_label.pack(anchor="w")

        snacks_buttons_frame = ttk.Frame(menu_frame)
        snacks_buttons_frame.pack(anchor="w", pady=(0, 10))

        for name, price in SNACKS_MENU.items():
            ttk.Button(
                snacks_buttons_frame,
                text=f"{name} (₹{price:.0f})",
                command=lambda n=name: self._on_item_selected(n),
            ).pack(fill="x", pady=1)

        qty_frame = ttk.Frame(menu_frame)
        qty_frame.pack(anchor="w", pady=(10, 0), fill="x")

        ttk.Label(qty_frame, text="Selected Item:").grid(row=0, column=0, sticky="w")
        ttk.Label(qty_frame, textvariable=self.selected_item_var, width=18).grid(
            row=0, column=1, sticky="w"
        )

        ttk.Label(qty_frame, text="Quantity:").grid(row=1, column=0, sticky="w", pady=(5, 0))
        ttk.Entry(qty_frame, textvariable=self.quantity_var, width=5).grid(
            row=1, column=1, sticky="w", pady=(5, 0)
        )

        ttk.Button(qty_frame, text="Add to Order", command=self._on_add_to_order).grid(
            row=2, column=0, columnspan=2, pady=8
        )

        ttk.Label(order_frame, text="Current Order", font=("Segoe UI", 10, "bold")).pack(
            anchor="w"
        )

        self.order_text = tk.Text(order_frame, height=15, state="disabled")
        self.order_text.pack(fill="both", expand=True, pady=(0, 10))

        bottom_frame = ttk.Frame(self.root, padding=10)
        bottom_frame.pack(fill="x")

        totals_frame = ttk.Frame(bottom_frame)
        totals_frame.pack(side="left")

        ttk.Label(totals_frame, text="Subtotal (₹):").grid(row=0, column=0, sticky="w")
        ttk.Label(totals_frame, textvariable=self.subtotal_var, width=10).grid(
            row=0, column=1, sticky="w"
        )

        ttk.Label(totals_frame, text="GST 5% (₹):").grid(row=1, column=0, sticky="w")
        ttk.Label(totals_frame, textvariable=self.gst_var, width=10).grid(
            row=1, column=1, sticky="w"
        )

        ttk.Label(totals_frame, text="Final Total (₹):").grid(row=2, column=0, sticky="w")
        ttk.Label(totals_frame, textvariable=self.total_var, width=10).grid(
            row=2, column=1, sticky="w"
        )

        payment_frame = ttk.Frame(bottom_frame)
        payment_frame.pack(side="right")

        ttk.Label(payment_frame, text="Payment Method:").grid(row=0, column=0, sticky="e")
        ttk.Combobox(
            payment_frame,
            textvariable=self.payment_method_var,
            values=PAYMENT_METHODS,
            state="readonly",
            width=10,
        ).grid(row=0, column=1, padx=5, sticky="w")

        ttk.Button(
            payment_frame,
            text="Generate Bill",
            command=self._on_generate_bill,
        ).grid(row=1, column=0, columnspan=2, pady=8)

    def _on_item_selected(self, item_name: str) -> None:
        self.selected_item_var.set(item_name)

    def _on_add_to_order(self) -> None:
        item_name = self.selected_item_var.get().strip()
        if not item_name:
            messagebox.showwarning("No item selected", "Please select an item first.")
            return

        qty_str = self.quantity_var.get().strip()
        if not qty_str.isdigit():
            messagebox.showwarning("Invalid quantity", "Quantity must be a whole number.")
            return

        try:
            qty = validate_quantity(int(qty_str))
        except ValueError as exc:
            messagebox.showwarning("Invalid quantity", str(exc))
            return

        unit_price = self.all_items.get(item_name)
        if unit_price is None:
            messagebox.showerror("Error", "Selected item not found in menu.")
            return

        self.order_items.append(
            OrderItem(name=item_name, quantity=qty, unit_price=unit_price)
        )
        self._refresh_order_display()
        self._recalculate_totals()

    def _refresh_order_display(self) -> None:
        self.order_text.configure(state="normal")
        self.order_text.delete("1.0", tk.END)

        if not self.order_items:
            self.order_text.insert(tk.END, "No items in order.\n")
        else:
            for item in self.order_items:
                self.order_text.insert(
                    tk.END,
                    f"{item.name} x{item.quantity} = ₹{item.line_total:.2f}\n",
                )

        self.order_text.configure(state="disabled")

    def _recalculate_totals(self) -> None:
        subtotal, gst_amount, final_total = calculate_totals(self.order_items)
        self.subtotal_var.set(f"{subtotal:.2f}")
        self.gst_var.set(f"{gst_amount:.2f}")
        self.total_var.set(f"{final_total:.2f}")

    def _on_generate_bill(self) -> None:
        customer_name = self.customer_name_var.get().strip()
        if not customer_name:
            messagebox.showwarning("Missing customer name", "Please enter customer name.")
            return

        if not self.order_items:
            messagebox.showwarning("Empty order", "Please add at least one item.")
            return

        payment_method = self.payment_method_var.get().strip()

        try:
            subtotal, gst_amount, final_total = save_transaction(
                customer_name=customer_name,
                order_items=self.order_items,
                payment_method=payment_method,
            )
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))
            return

        messagebox.showinfo(
            "Bill Generated",
            f"Customer: {customer_name}\n"
            f"Subtotal: ₹{subtotal:.2f}\n"
            f"GST (5%): ₹{gst_amount:.2f}\n"
            f"Final Total: ₹{final_total:.2f}\n"
            f"Payment Method: {payment_method}\n\n"
            "Transaction saved to sales.csv",
        )

        self.order_items.clear()
        self._refresh_order_display()
        self._recalculate_totals()
        self.quantity_var.set("1")


def run_gui() -> None:
    app = PosGUI()
    app.root.mainloop()


# =============================================================================
# 5. SMART POS ENTRY (ADMIN LOGIN + GUI CHOICE)
# =============================================================================

ADMIN_PASSWORD = "admin123"


def _admin_login_flow() -> None:
    print("\n=== ADMIN LOGIN ===")
    password = input("Enter admin password: ").strip()
    if password != ADMIN_PASSWORD:
        print("Incorrect password. Access denied.")
        return

    print("Login successful.")
    show_daily_report()


def _customer_gui_flow() -> None:
    print("Launching Smart POS GUI...")
    run_gui()


def smart_pos_main() -> None:
    print("====================================")
    print("      SMART POS - BILLING SYSTEM    ")
    print("====================================")
    print("1. Admin (Daily Sales Report)")
    print("2. Customer (Billing GUI)")

    choice = input("Enter your choice (1 or 2): ").strip()

    if choice == "1":
        _admin_login_flow()
    elif choice == "2":
        _customer_gui_flow()
    else:
        print("Invalid choice. Exiting.")


# =============================================================================
# 6. TOP-LEVEL ENTRY: CHOOSE COFFEEBOT OR SMART POS
# =============================================================================


def main() -> None:
    print_welcome()
    print("Choose an option:")
    print("1. Simple Coffee Bot (console ordering)")
    print("2. Smart POS (admin/GUI system)")

    choice = input("Enter 1 or 2: ").strip()

    if choice == "1":
        coffeebot_cli_main()
    elif choice == "2":
        smart_pos_main()
    else:
        print("Invalid choice. Exiting.")


if __name__ == "__main__":
    main()
