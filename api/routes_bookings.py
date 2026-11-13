"""
FastAPI route handlers for booking operations (create, list, release, cancel).
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from database.connection import get_db
from services.booking_service import (
    add_booking,
    list_all_bookings,
    release_active_booking,
    cancel_active_booking,
    NotFoundError,
    ConflictError,
)
from api.schemas import BookingCreateRequest, BookingResponse

router = APIRouter(prefix="/api", tags=["Bookings"])


@router.post("/bookings", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_new_booking(body: BookingCreateRequest):
    """Create a new active parking booking for an available slot."""
    with get_db() as conn:
        try:
            booking = add_booking(
                conn,
                slot_id=body.slot_id,
                vehicle_number=body.vehicle_number,
                vehicle_type=body.vehicle_type,
                driver_name=body.driver_name,
            )
            return booking
        except NotFoundError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except ConflictError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/bookings", response_model=List[BookingResponse])
def get_bookings(status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (active, completed, cancelled)")):
    """Retrieve all bookings sorted newest first, with optional status filter."""
    with get_db() as conn:
        return list_all_bookings(conn, status=status_filter)


@router.put("/bookings/{booking_id}/release", response_model=BookingResponse)
def release_booking_endpoint(booking_id: int):
    """End an active booking, calculate total duration fee, and release the slot."""
    with get_db() as conn:
        try:
            released_booking = release_active_booking(conn, booking_id)
            return released_booking
        except NotFoundError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except ConflictError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete("/bookings/{booking_id}", response_model=BookingResponse)
def cancel_booking_endpoint(booking_id: int):
    """Cancel an active booking and free the assigned slot."""
    with get_db() as conn:
        try:
            cancelled_booking = cancel_active_booking(conn, booking_id)
            return cancelled_booking
        except NotFoundError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except ConflictError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
