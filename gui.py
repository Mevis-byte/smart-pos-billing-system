"""
Tkinter GUI for the Smart POS billing system.

This module focuses only on user interface concerns and delegates:
- Pricing, GST, and totals to `pos_logic`
- Transaction persistence to `pos_logic.save_transaction`
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import List

from pos_logic import (
    DRINKS_MENU,
    SNACKS_MENU,
    OrderItem,
    calculate_totals,
    get_all_items,
    save_transaction,
    validate_quantity,
)


PAYMENT_METHODS = ("Cash", "Card", "UPI")


class PosGUI:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Smart POS - Billing System")
        self.root.geometry("800x500")

        # Business state
        self.order_items: List[OrderItem] = []
        self.all_items = get_all_items()

        # Tk variables
        self.customer_name_var = tk.StringVar()
        self.quantity_var = tk.StringVar(value="1")
        self.selected_item_var = tk.StringVar(value="")
        self.payment_method_var = tk.StringVar(value=PAYMENT_METHODS[0])
        self.subtotal_var = tk.StringVar(value="0.00")
        self.gst_var = tk.StringVar(value="0.00")
        self.total_var = tk.StringVar(value="0.00")

        self._build_layout()

    # --- UI construction ----------------------------------------------------

    def _build_layout(self) -> None:
        # Top: customer name
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill="x")

        ttk.Label(top_frame, text="Customer Name:").pack(side="left")
        ttk.Entry(top_frame, textvariable=self.customer_name_var, width=30).pack(
            side="left", padx=5
        )

        # Center: left = menus, right = order display
        center_frame = ttk.Frame(self.root, padding=10)
        center_frame.pack(fill="both", expand=True)

        menu_frame = ttk.Frame(center_frame)
        menu_frame.pack(side="left", fill="y", padx=(0, 10))

        order_frame = ttk.Frame(center_frame)
        order_frame.pack(side="right", fill="both", expand=True)

        # Drinks buttons
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

        # Snacks buttons
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

        # Quantity + Add to order
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

        # Order display area
        ttk.Label(order_frame, text="Current Order", font=("Segoe UI", 10, "bold")).pack(
            anchor="w"
        )

        self.order_text = tk.Text(order_frame, height=15, state="disabled")
        self.order_text.pack(fill="both", expand=True, pady=(0, 10))

        # Bottom: totals, payment, generate bill
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

    # --- Event handlers -----------------------------------------------------

    def _on_item_selected(self, item_name: str) -> None:
        """Handle clicks on menu buttons - select an item for adding."""
        self.selected_item_var.set(item_name)

    def _on_add_to_order(self) -> None:
        """Add the currently selected item with the specified quantity."""
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
        """Redraw the order text area with current items."""
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
        """Validate data, save transaction and show confirmation."""
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

        # Reset order for next customer
        self.order_items.clear()
        self._refresh_order_display()
        self._recalculate_totals()
        self.quantity_var.set("1")


def run_gui() -> None:
    """Launch the Tkinter GUI."""
    app = PosGUI()
    app.root.mainloop()


if __name__ == "__main__":
    run_gui()

