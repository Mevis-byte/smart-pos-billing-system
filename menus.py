"""
Menu definitions and tax configuration for the Smart POS system.
Uses simple dictionaries so both CLI and GUI can share the same data.
"""

DRINKS_MENU = {
    "Latte": 120.0,
    "Espresso": 100.0,
    "Cappuccino": 130.0,
    "Black Coffee": 90.0,
    "Masala Tea": 60.0,
}

SNACKS_MENU = {
    "Vada pav": 30.0,
    "Samosa": 25.0,
    "Grilled Sandwich": 70.0,
    "French Fries": 80.0,
    "Chocolate Donut": 60.0,
}

# 5% GST applied on subtotal
GST_RATE = 0.05


def get_all_items():
    """
    Return a single dictionary with all menu items merged.
    Keys are item names, values are unit prices.
    """
    all_items = {}
    all_items.update(DRINKS_MENU)
    all_items.update(SNACKS_MENU)
    return all_items

