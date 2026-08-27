def apply_discount(price: float, pct: float) -> float:
    """Apply a percentage discount to price."""
    return price * (1 - pct / 100)
