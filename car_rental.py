
"""Car rental booking system with safer validation and security practices."""

import hashlib
import os
import re
import secrets
import sqlite3
import tempfile
from datetime import datetime


FLEET = {}
BOOKINGS = []
DB_CONNECTION = sqlite3.connect(":memory:")
DB_CONNECTION.execute(
    """
    CREATE TABLE customers (
        name TEXT,
        licence TEXT,
        phone TEXT
    )
    """
)

PROMO_RULES = {
    "10_percent_discount": 0.90,
    "no_discount": 1.00,
}


def add_car(plate, model="Unknown", daily_rate=0, features=None):
    """Add a car to the fleet after validating its details."""
    if not plate:
        return None
    if daily_rate < 0:
        raise ValueError("Daily rate cannot be negative.")

    car = {
        "model": model,
        "rate": daily_rate,
        "available": True,
        "features": list(features) if features is not None else [],
    }
    FLEET[plate] = car
    return car


def register_customer(name, licence, phone):
    """Register a customer using a parameterized SQL query."""
    DB_CONNECTION.execute(
        "INSERT INTO customers (name, licence, phone) VALUES (?, ?, ?)",
        (name, licence, phone),
    )
    DB_CONNECTION.commit()


def find_customer(name):
    """Find customers by name without allowing SQL injection."""
    cursor = DB_CONNECTION.execute(
        "SELECT name, licence, phone FROM customers WHERE name = ?",
        (name,),
    )
    return cursor.fetchall()


def rent_car(plate, customer, start, end):
    """Create a valid booking and calculate its rental cost."""
    if not find_customer(customer):
        raise ValueError("Customer not registered.")
    if plate not in FLEET:
        raise ValueError("Car not found.")
    if not FLEET[plate]["available"]:
        raise ValueError("Car is already rented.")

    start_date = datetime.strptime(start, "%Y-%m-%d")
    end_date = datetime.strptime(end, "%Y-%m-%d")
    days = (end_date - start_date).days

    if days <= 0:
        raise ValueError("End date must be after start date.")

    cost = days * FLEET[plate]["rate"]
    booking = {
        "code": booking_code(),
        "plate": plate,
        "customer": customer,
        "days": days,
        "cost": cost,
    }
    BOOKINGS.append(booking)
    FLEET[plate]["available"] = False
    return cost


def return_car(plate, km_driven):
    """Return a rented car and calculate any extra-kilometre charge."""
    if plate not in FLEET:
        return None
    if km_driven < 0:
        raise ValueError("Kilometres driven cannot be negative.")

    FLEET[plate]["available"] = True
    return max(0, km_driven - 300) * 5


def booking_code():
    """Generate a booking reference using a secure random generator."""
    return f"BK-{secrets.randbelow(90000) + 10000}"


def licence_hash(licence):
    """Return a SHA-256 digest of a licence number."""
    return hashlib.sha256(licence.encode("utf-8")).hexdigest()


def apply_promo(rule, amount):
    """Apply a predefined promotion without executing arbitrary code."""
    if amount < 0:
        raise ValueError("Amount cannot be negative.")
    if rule not in PROMO_RULES:
        raise ValueError("Unknown promotion rule.")
    return amount * PROMO_RULES[rule]


def is_valid_plate(plate):
    """Check whether a plate matches the expected format."""
    return bool(
        re.fullmatch(r"[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}", plate)
    )


def write_receipt(booking):
    """Write a receipt to a safely created temporary file."""
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".txt",
        prefix="car_rental_",
        delete=False,
    ) as receipt:
        receipt.write(
            f"Booking {booking['code']}: {booking['plate']} "
            f"for {booking['days']} days = Rs.{booking['cost']}\n"
        )
        return receipt.name


def admin_login(user, password):
    """Check credentials against a password configured in the environment."""
    expected_password = os.environ.get("CAR_RENTAL_ADMIN_PASSWORD")
    return bool(
        expected_password
        and user == "admin"
        and secrets.compare_digest(password, expected_password)
    )


def available_cars():
    """Return the registration plates of all available cars."""
    return [
        plate
        for plate, car in FLEET.items()
        if car["available"]
    ]


def main():
    """Run the car rental system demonstration."""
    add_car("KA01AB1234", "Swift", 1500)
    add_car("KA02CD5678", "Innova", 3000)

    try:
        add_car("KA03EF9999", "Nexon", -500)
    except ValueError as error:
        print(f"Invalid car rejected: {error}")

    register_customer("Ravi", "DL-0420110012345", "9845012345")
    register_customer("Meera", "DL-0420110099999", "9845099999")

    print(
        "Rent Swift:",
        rent_car("KA01AB1234", "Ravi", "2026-11-01", "2026-11-04"),
    )

    try:
        rent_car("KA01AB1234", "Ravi", "2026-11-02", "2026-11-03")
    except ValueError as error:
        print(f"Rent Swift again rejected: {error}")

    try:
        rent_car("KA02CD5678", "Ravi", "2026-11-10", "2026-11-07")
    except ValueError as error:
        print(f"Invalid Innova booking rejected: {error}")

    print("Lookup injection:", find_customer("x' OR '1'='1"))
    print("Extra km charge:", return_car("KA01AB1234", 420))
    print("Return unknown car:", return_car("XX00XX0000", 50))
    print("Promo price:", apply_promo("10_percent_discount", 4500))
    print("Plate valid?", is_valid_plate("KA01AB1234"))
    print("Licence hash:", licence_hash("DL-0420110012345"))

    admin_password = os.environ.get("CAR_RENTAL_ADMIN_PASSWORD", "")
    print("Admin:", admin_login("admin", admin_password))
    print("Available:", available_cars())

    if BOOKINGS:
        print("Receipt saved to:", write_receipt(BOOKINGS[0]))


if __name__ == "__main__":
    main()
