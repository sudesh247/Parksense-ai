"""
Deterministic seed data generator for ParkSense AI database.
"""

import random
from datetime import datetime, timedelta, timezone
from database.connection import get_db
from database.queries import init_db
from utils.helpers import calculate_parking_fee
from utils.logger import logger

SEED_RANDOM_STATE = 42

VEHICLE_NUMBERS_PREFIXES = ["MH01", "MH02", "MH03", "MH12", "MH14", "KA01", "KA03", "DL01", "HR26", "TN07"]
DRIVER_NAMES = [
    "Aarav Sharma", "Aditi Patel", "Rohan Mehta", "Priya Singh", "Vikram Malhotra",
    "Ananya Iyer", "Karan Gupta", "Neha Verma", "Siddharth Joshi", "Pooja Reddy",
    "Rahul Deshmukh", "Sneha Nair", "Amitabh Roy", "Divya Kapoor", "Varun Bhatia",
    "Tanvi Saxena", "Nikhil Kumar", "Meera Chawla", "Rajesh Pillai", "Kavita Rao"
]


def generate_seed_slots() -> list[dict]:
    """Generate 60 realistic slots across 4 floors."""
    slots = []
    slot_id_counter = 1

    floor_prefixes = {1: "A", 2: "B", 3: "C", 4: "D"}

    # Fixed designations to meet requirements exactly:
    # 12 EV slots, 6 disabled-friendly, 8 reserved
    ev_slot_indices = {2, 5, 8, 12, 18, 22, 27, 33, 38, 44, 49, 55}
    disabled_indices = {1, 3, 16, 17, 31, 32}
    reserved_indices = {10, 15, 25, 30, 40, 45, 50, 60}
    near_exit_indices = {1, 2, 3, 4, 16, 17, 18, 19, 31, 32, 33, 34, 46, 47, 48, 49}

    for floor in range(1, 5):
        prefix = floor_prefixes[floor]
        for num in range(1, 16):
            idx = (floor - 1) * 15 + num
            slot_number = f"F{floor}-{prefix}{num:02d}"

            # Vehicle type selection
            if idx in {5, 15, 25, 35, 45, 55}:
                v_type = "bike"
            elif idx in {10, 20, 30, 40, 50, 60}:
                v_type = "suv"
            else:
                v_type = "car"

            is_ev = 1 if idx in ev_slot_indices else 0
            is_disabled = 1 if idx in disabled_indices else 0
            is_res = 1 if idx in reserved_indices else 0
            is_exit = 1 if idx in near_exit_indices else 0

            # Base price calculation
            if v_type == "bike":
                base_price = 20.0
            elif v_type == "car":
                base_price = 40.0 if floor <= 2 else 35.0
            else:  # suv
                base_price = 60.0

            if is_ev:
                base_price += 10.0

            slots.append({
                "id": slot_id_counter,
                "slot_number": slot_number,
                "floor": floor,
                "status": "reserved" if is_res else "available",
                "price_per_hour": base_price,
                "vehicle_type": v_type,
                "is_ev": is_ev,
                "near_exit": is_exit,
                "is_reserved": is_res,
                "is_disabled_friendly": is_disabled,
            })
            slot_id_counter += 1

    return slots


def seed_database_if_empty() -> None:
    """Populate database with slots and 14 days of realistic booking data if empty."""
    with get_db() as conn:
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as cnt FROM slots")
        count = cursor.fetchone()["cnt"]
        if count > 0:
            logger.info("Database already seeded. Skipping seed execution.")
            return

        logger.info("Seeding database with 60 slots and historical bookings...")
        random.seed(SEED_RANDOM_STATE)

        slots = generate_seed_slots()

        for s in slots:
            cursor.execute(
                """
                INSERT INTO slots (id, slot_number, floor, status, price_per_hour, vehicle_type, is_ev, near_exit, is_reserved, is_disabled_friendly)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    s["id"], s["slot_number"], s["floor"], s["status"], s["price_per_hour"],
                    s["vehicle_type"], s["is_ev"], s["near_exit"], s["is_reserved"], s["is_disabled_friendly"]
                )
            )

        # Generate bookings over the last 14 days up to today
        now = datetime.now(timezone.utc)
        bookings = []

        # Non-reserved slots pool for random assignment
        available_slot_ids = [s["id"] for s in slots if not s["is_reserved"]]

        # 1. Historical completed bookings for days -14 to -1
        for days_ago in range(14, 0, -1):
            day_base = now - timedelta(days=days_ago)
            # 5 to 7 bookings per historical day
            daily_count = random.randint(5, 7)

            for _ in range(daily_count):
                slot_id = random.choice(available_slot_ids)
                slot = next(s for s in slots if s["id"] == slot_id)

                # Morning and evening peak entry times
                peak_hour = random.choice([8, 9, 10, 11, 14, 17, 18, 19])
                minute = random.randint(0, 59)
                entry_dt = day_base.replace(hour=peak_hour, minute=minute, second=0, microsecond=0)

                # Duration between 1 and 6 hours
                duration_hours = random.randint(1, 6)
                exit_dt = entry_dt + timedelta(hours=duration_hours)

                veh_prefix = random.choice(VEHICLE_NUMBERS_PREFIXES)
                veh_num = f"{veh_prefix}-{random.randint(1000, 9999)}"
                driver = random.choice(DRIVER_NAMES)

                fee = calculate_parking_fee(entry_dt.isoformat(), exit_dt.isoformat(), slot["price_per_hour"])

                bookings.append({
                    "slot_id": slot_id,
                    "vehicle_number": veh_num,
                    "vehicle_type": slot["vehicle_type"],
                    "driver_name": driver,
                    "entry_time": entry_dt.isoformat(),
                    "exit_time": exit_dt.isoformat(),
                    "amount": fee,
                    "status": "completed",
                })

        # 2. Today's bookings (~12 total: 8 completed, 4 active)
        active_occupied_slots = random.sample(available_slot_ids, 5)

        # Today's completed
        for _ in range(8):
            slot_id = random.choice(available_slot_ids)
            slot = next(s for s in slots if s["id"] == slot_id)
            entry_hour = random.randint(6, 12)
            entry_dt = now.replace(hour=entry_hour, minute=random.randint(0, 59), second=0, microsecond=0)
            duration_hours = random.randint(1, 4)
            exit_dt = entry_dt + timedelta(hours=duration_hours)

            veh_prefix = random.choice(VEHICLE_NUMBERS_PREFIXES)
            veh_num = f"{veh_prefix}-{random.randint(1000, 9999)}"
            driver = random.choice(DRIVER_NAMES)

            fee = calculate_parking_fee(entry_dt.isoformat(), exit_dt.isoformat(), slot["price_per_hour"])

            bookings.append({
                "slot_id": slot_id,
                "vehicle_number": veh_num,
                "vehicle_type": slot["vehicle_type"],
                "driver_name": driver,
                "entry_time": entry_dt.isoformat(),
                "exit_time": exit_dt.isoformat(),
                "amount": fee,
                "status": "completed",
            })

        # Today's active bookings
        for slot_id in active_occupied_slots:
            slot = next(s for s in slots if s["id"] == slot_id)
            entry_hour = max(0, now.hour - random.randint(1, 3))
            entry_dt = now.replace(hour=entry_hour, minute=random.randint(0, 59), second=0, microsecond=0)

            veh_prefix = random.choice(VEHICLE_NUMBERS_PREFIXES)
            veh_num = f"{veh_prefix}-{random.randint(1000, 9999)}"
            driver = random.choice(DRIVER_NAMES)

            bookings.append({
                "slot_id": slot_id,
                "vehicle_number": veh_num,
                "vehicle_type": slot["vehicle_type"],
                "driver_name": driver,
                "entry_time": entry_dt.isoformat(),
                "exit_time": None,
                "amount": None,
                "status": "active",
            })

            # Set slot status to occupied
            cursor.execute("UPDATE slots SET status = 'occupied' WHERE id = ?", (slot_id,))

        # Insert all generated bookings
        for b in bookings:
            cursor.execute(
                """
                INSERT INTO bookings (slot_id, vehicle_number, vehicle_type, driver_name, entry_time, exit_time, amount, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (b["slot_id"], b["vehicle_number"], b["vehicle_type"], b["driver_name"], b["entry_time"], b["exit_time"], b["amount"], b["status"])
            )

        logger.info(f"Database seeded successfully with {len(slots)} slots and {len(bookings)} bookings.")


if __name__ == "__main__":
    seed_database_if_empty()
