"""
Booking management business logic including single-source billing and slot status synchronization.
"""

import sqlite3
from typing import List, Dict, Any, Optional
from database.queries import (
    get_slot_by_id,
    update_slot_status,
    create_booking,
    get_booking_by_id,
    get_all_bookings,
    release_booking,
    update_booking_status,
)
from utils.helpers import get_current_iso_timestamp, calculate_parking_fee


class ServiceError(Exception):
    """Base domain exception for service logic errors."""
    pass


class NotFoundError(ServiceError):
    """Resource not found domain error."""
    pass


class ConflictError(ServiceError):
    """Resource state conflict domain error."""
    pass


def add_booking(
    conn: sqlite3.Connection,
    slot_id: int,
    vehicle_number: str,
    vehicle_type: str,
    driver_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new active booking for an available slot.
    Raises NotFoundError if slot missing, ConflictError if slot unavailable.
    """
    slot = get_slot_by_id(conn, slot_id)
    if not slot:
        raise NotFoundError(f"Slot with ID {slot_id} not found.")

    if slot["status"] != "available":
        raise ConflictError(f"Slot '{slot['slot_number']}' is currently {slot['status']} and cannot be booked.")

    entry_time = get_current_iso_timestamp()
    booking_id = create_booking(
        conn,
        slot_id=slot_id,
        vehicle_number=vehicle_number.upper().strip(),
        vehicle_type=vehicle_type.lower().strip(),
        driver_name=driver_name.strip() if driver_name else None,
        entry_time=entry_time,
        status="active",
    )

    # Mark slot as occupied
    update_slot_status(conn, slot_id, "occupied")

    created_booking = get_booking_by_id(conn, booking_id)
    return created_booking


def list_all_bookings(conn: sqlite3.Connection, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all bookings, optionally filtered by status."""
    return get_all_bookings(conn, status=status)


def release_active_booking(conn: sqlite3.Connection, booking_id: int) -> Dict[str, Any]:
    """
    Complete an active booking, compute duration fee, and release the slot.
    Raises NotFoundError if booking missing, ConflictError if already released/cancelled.
    """
    booking = get_booking_by_id(conn, booking_id)
    if not booking:
        raise NotFoundError(f"Booking with ID {booking_id} not found.")

    if booking["status"] != "active":
        raise ConflictError(f"Booking {booking_id} is already '{booking['status']}' and cannot be released.")

    exit_time = get_current_iso_timestamp()
    price_per_hour = booking["price_per_hour"]

    # Calculate fee using central billing function
    amount = calculate_parking_fee(booking["entry_time"], exit_time, price_per_hour)

    # Update database record
    release_booking(conn, booking_id, exit_time=exit_time, amount=amount)

    # Free the slot
    update_slot_status(conn, booking["slot_id"], "available")

    return get_booking_by_id(conn, booking_id)


def cancel_active_booking(conn: sqlite3.Connection, booking_id: int) -> Dict[str, Any]:
    """
    Cancel an active booking and free the assigned slot.
    Raises NotFoundError if missing, ConflictError if not active.
    """
    booking = get_booking_by_id(conn, booking_id)
    if not booking:
        raise NotFoundError(f"Booking with ID {booking_id} not found.")

    if booking["status"] != "active":
        raise ConflictError(f"Booking {booking_id} is '{booking['status']}' and cannot be cancelled.")

    # Update booking status
    update_booking_status(conn, booking_id, "cancelled")

    # Free the slot
    update_slot_status(conn, booking["slot_id"], "available")

    return get_booking_by_id(conn, booking_id)
