"""
Parameterized SQL query functions for ParkSense AI database operations.
"""

import sqlite3
from typing import List, Dict, Any, Optional
from config.settings import settings


def init_db(conn: sqlite3.Connection) -> None:
    """Execute schema.sql to create database tables and indexes if they do not exist."""
    schema_path = settings.DATABASE_PATH.parent / "schema.sql"
    if schema_path.exists():
        with open(schema_path, "r", encoding="utf-8") as f:
            conn.executescript(f.read())


# --- SLOT QUERIES ---

def get_all_slots(
    conn: sqlite3.Connection,
    floor: Optional[int] = None,
    status: Optional[str] = None,
    vehicle_type: Optional[str] = None,
    is_ev: Optional[int] = None,
    is_disabled_friendly: Optional[int] = None,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieve filtered slots."""
    query = "SELECT * FROM slots WHERE 1=1"
    params: List[Any] = []

    if floor is not None:
        query += " AND floor = ?"
        params.append(floor)
    if status:
        query += " AND status = ?"
        params.append(status)
    if vehicle_type:
        query += " AND vehicle_type = ?"
        params.append(vehicle_type)
    if is_ev is not None:
        query += " AND is_ev = ?"
        params.append(is_ev)
    if is_disabled_friendly is not None:
        query += " AND is_disabled_friendly = ?"
        params.append(is_disabled_friendly)
    if search:
        query += " AND slot_number LIKE ?"
        params.append(f"%{search}%")

    query += " ORDER BY floor ASC, slot_number ASC"
    cursor = conn.cursor()
    cursor.execute(query, params)
    return cursor.fetchall()


def get_slot_by_id(conn: sqlite3.Connection, slot_id: int) -> Optional[Dict[str, Any]]:
    """Fetch a single slot by ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM slots WHERE id = ?", (slot_id,))
    return cursor.fetchone()


def get_slot_by_number(conn: sqlite3.Connection, slot_number: str) -> Optional[Dict[str, Any]]:
    """Fetch a single slot by slot_number."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM slots WHERE slot_number = ?", (slot_number,))
    return cursor.fetchone()


def update_slot_status(conn: sqlite3.Connection, slot_id: int, status: str) -> None:
    """Update slot status ('available', 'occupied', 'reserved')."""
    cursor = conn.cursor()
    cursor.execute("UPDATE slots SET status = ? WHERE id = ?", (status, slot_id))


def get_floors_summary(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Retrieve floor-wise count breakdown."""
    query = """
    SELECT 
        floor,
        COUNT(*) as total_slots,
        SUM(CASE WHEN status = 'available' THEN 1 ELSE 0 END) as available_slots,
        SUM(CASE WHEN status = 'occupied' THEN 1 ELSE 0 END) as occupied_slots,
        SUM(CASE WHEN status = 'reserved' THEN 1 ELSE 0 END) as reserved_slots
    FROM slots
    GROUP BY floor
    ORDER BY floor ASC
    """
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchall()


# --- BOOKING QUERIES ---

def create_booking(
    conn: sqlite3.Connection,
    slot_id: int,
    vehicle_number: str,
    vehicle_type: str,
    driver_name: Optional[str],
    entry_time: str,
    status: str = "active",
) -> int:
    """Insert a new booking record into the database."""
    query = """
    INSERT INTO bookings (slot_id, vehicle_number, vehicle_type, driver_name, entry_time, status)
    VALUES (?, ?, ?, ?, ?, ?)
    """
    cursor = conn.cursor()
    cursor.execute(query, (slot_id, vehicle_number, vehicle_type, driver_name, entry_time, status))
    return cursor.lastrowid


def get_booking_by_id(conn: sqlite3.Connection, booking_id: int) -> Optional[Dict[str, Any]]:
    """Fetch a single booking by ID with slot info."""
    query = """
    SELECT b.*, s.slot_number, s.floor, s.price_per_hour
    FROM bookings b
    JOIN slots s ON b.slot_id = s.id
    WHERE b.id = ?
    """
    cursor = conn.cursor()
    cursor.execute(query, (booking_id,))
    return cursor.fetchone()


def get_active_booking_for_slot(conn: sqlite3.Connection, slot_id: int) -> Optional[Dict[str, Any]]:
    """Check if there is an active booking for a slot."""
    query = "SELECT * FROM bookings WHERE slot_id = ? AND status = 'active'"
    cursor = conn.cursor()
    cursor.execute(query, (slot_id,))
    return cursor.fetchone()


def get_all_bookings(conn: sqlite3.Connection, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """List bookings joined with slot details, sorted newest first."""
    query = """
    SELECT b.*, s.slot_number, s.floor, s.price_per_hour
    FROM bookings b
    JOIN slots s ON b.slot_id = s.id
    """
    params: List[Any] = []
    if status:
        query += " WHERE b.status = ?"
        params.append(status)

    query += " ORDER BY b.entry_time DESC"
    cursor = conn.cursor()
    cursor.execute(query, params)
    return cursor.fetchall()


def release_booking(conn: sqlite3.Connection, booking_id: int, exit_time: str, amount: float) -> None:
    """Complete a booking by setting exit_time, amount, and status = 'completed'."""
    query = """
    UPDATE bookings 
    SET exit_time = ?, amount = ?, status = 'completed'
    WHERE id = ?
    """
    cursor = conn.cursor()
    cursor.execute(query, (exit_time, amount, booking_id))


def update_booking_status(conn: sqlite3.Connection, booking_id: int, status: str) -> None:
    """Update status of a booking (e.g. 'cancelled')."""
    cursor = conn.cursor()
    cursor.execute("UPDATE bookings SET status = ? WHERE id = ?", (status, booking_id))


# --- ANALYTICS QUERIES ---

def get_raw_slots_for_analytics(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Fetch all slots for Pandas analytical calculations."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM slots")
    return cursor.fetchall()


def get_raw_bookings_for_analytics(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Fetch all bookings with slot pricing info for Pandas analytics."""
    query = """
    SELECT b.*, s.slot_number, s.floor, s.price_per_hour
    FROM bookings b
    JOIN slots s ON b.slot_id = s.id
    """
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchall()
