"""
Entry point for the Smart POS billing system.

At startup, user can choose:
- Admin login: view today's sales report (console) and exit
- Customer billing: open the Tkinter GUI for order taking and billing
"""

from __future__ import annotations

from admin import show_daily_report
from gui import run_gui


ADMIN_PASSWORD = "admin123"


def _admin_login_flow() -> None:
    """Prompt for admin password and, if valid, show the daily report."""
    print("\n=== ADMIN LOGIN ===")
    password = input("Enter admin password: ").strip()
    if password != ADMIN_PASSWORD:
        print("Incorrect password. Access denied.")
        return

    print("Login successful.")
    show_daily_report()


def _customer_gui_flow() -> None:
    """Launch the Tkinter POS GUI for customer billing."""
    print("Launching Smart POS GUI...")
    run_gui()


def main() -> None:
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


if __name__ == "__main__":
    main()

