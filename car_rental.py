"""Car rental booking system.

Manages a fleet, customers (SQLite), bookings, promo rules, plate validation,
licence hashing, admin login and booking receipts.
"""

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import tempfile
from datetime import datetime

DATE_FORMAT = "%Y-%m-%d"
FREE_KM = 300
EXTRA_KM_RATE = 5
PLATE_PATTERN = re.compile(r"[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}")
# Salt for licence hashing; override via the LICENCE_SALT env variable.
LICENCE_SALT = os.environ.get("LICENCE_SALT", "car-rental-demo-salt")

# Rental state (mutated in place, hence upper-case module constants)
FLEET = {}
BOOKINGS = []
CONN = sqlite3.connect(":memory:")
CONN.execute("CREATE TABLE customers (name TEXT, licence TEXT, phone TEXT)")


def add_car(plate, model="Unknown", daily_rate=0, features=None):
    """Add a car to the fleet and return its record."""
    if not plate:
        raise ValueError("Plate is required")
    if daily_rate < 0:
        raise ValueError(f"Daily rate cannot be negative: {daily_rate}")
    FLEET[plate] = {
        "model": model,
        "rate": daily_rate,
        "available": True,
        "features": list(features) if features else [],
    }
    return FLEET[plate]


def register_customer(name, licence, phone):
    """Store a customer using a parameterised query (no SQL injection)."""
    CONN.execute(
        "INSERT INTO customers VALUES (?, ?, ?)", (name, licence, phone)
    )


def find_customer(name):
    """Return all customers with the given name."""
    return CONN.execute(
        "SELECT * FROM customers WHERE name = ?", (name,)
    ).fetchall()


def rent_car(plate, customer, start, end):
    """Create a booking and return its cost."""
    if not find_customer(customer):
        raise ValueError("Customer not registered")
    if plate not in FLEET:
        raise ValueError(f"Unknown car: {plate}")
    if not FLEET[plate]["available"]:
        raise ValueError(f"Car {plate} is already rented")
    days = (
        datetime.strptime(end, DATE_FORMAT)
        - datetime.strptime(start, DATE_FORMAT)
    ).days
    if days <= 0:
        raise ValueError("End date must be after start date")
    cost = days * FLEET[plate]["rate"]
    FLEET[plate]["available"] = False
    BOOKINGS.append({
        "code": booking_code(),
        "plate": plate,
        "customer": customer,
        "days": days,
        "cost": cost,
    })
    return cost


def return_car(plate, km_driven):
    """Mark a car returned and return any extra-kilometre charge."""
    if plate not in FLEET:
        raise ValueError(f"Unknown car: {plate}")
    FLEET[plate]["available"] = True
    return max(0, km_driven - FREE_KM) * EXTRA_KM_RATE


def booking_code():
    """Return a booking code that is not already in use."""
    existing = {b["code"] for b in BOOKINGS}
    while True:
        code = f"BK-{secrets.randbelow(90000) + 10000}"
        if code not in existing:
            return code


def licence_hash(licence):
    """Return a salted SHA-256 hash of a licence number."""
    return hashlib.sha256((LICENCE_SALT + licence).encode()).hexdigest()


def apply_promo(rule, amount):
    """Apply a promo rule to an amount without executing code.

    Supported rules: "percent:10" (10% off) and "flat:200" (Rs.200 off).
    """
    kind, _, raw_value = rule.partition(":")
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(f"Invalid promo rule: {rule!r}") from exc
    if kind == "percent" and 0 <= value <= 100:
        return amount * (1 - value / 100)
    if kind == "flat" and value >= 0:
        return max(0, amount - value)
    raise ValueError(f"Invalid promo rule: {rule!r}")


def is_valid_plate(plate):
    """Return True if the plate matches the Indian registration format."""
    return PLATE_PATTERN.fullmatch(plate) is not None


def write_receipt(booking):
    """Write a booking receipt to a private temporary file; return its path."""
    file_descriptor, path = tempfile.mkstemp(suffix=".txt")
    with os.fdopen(file_descriptor, "w", encoding="utf-8") as receipt:
        receipt.write(
            f"Booking {booking['code']}: {booking['plate']} for "
            f"{booking['days']} days = Rs.{booking['cost']}\n"
        )
    os.chmod(path, 0o600)
    return path


def admin_login(user, password):
    """Check admin credentials against the ADMIN_PASSWORD env variable."""
    expected = os.environ.get("ADMIN_PASSWORD")
    if not expected or user != "admin":
        return False
    return hmac.compare_digest(password.encode(), expected.encode())


def available_cars():
    """Return the plates of all cars currently available."""
    return [plate for plate, car in FLEET.items() if car["available"]]


def try_call(label, func, *args):
    """Run func and print its result, or the validation error it raises."""
    try:
        print(f"{label}:", func(*args))
    except ValueError as error:
        print(f"{label}: rejected - {error}")


def main():
    """Run a short demo of the rental system."""
    try_call("Add Nexon (negative rate)", add_car, "KA03EF9999", "Nexon", -500)
    add_car("KA01AB1234", "Swift", 1500)
    add_car("KA02CD5678", "Innova", 3000)
    register_customer("Ravi", "DL-0420110012345", "9845012345")
    register_customer("Meera", "DL-0420110099999", "9845099999")
    try_call("Rent Swift", rent_car, "KA01AB1234", "Ravi",
             "2026-11-01", "2026-11-04")
    try_call("Rent Swift again", rent_car, "KA01AB1234", "Ravi",
             "2026-11-02", "2026-11-03")
    try_call("Rent Innova (bad dates)", rent_car, "KA02CD5678", "Ravi",
             "2026-11-10", "2026-11-07")
    print("Lookup injection:", find_customer("x' OR '1'='1"))
    try_call("Extra km charge", return_car, "KA01AB1234", 420)
    try_call("Return unknown car", return_car, "XX00XX0000", 50)
    try_call("Promo price", apply_promo, "percent:10", 4500)
    try_call("Bad promo rule", apply_promo, "amount = 0", 4500)
    print("Plate valid?", is_valid_plate("KA01AB1234"))
    print("Licence hash:", licence_hash("DL-0420110012345"))
    print("Admin (no password configured):", admin_login("admin", "guess"))
    print("Available:", available_cars())
    print("Receipt saved to:", write_receipt(BOOKINGS[0]))


if __name__ == "__main__":
    main()
