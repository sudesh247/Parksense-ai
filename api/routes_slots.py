"""
FastAPI route handlers for parking slots and floor summaries.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from database.connection import get_db
from services.slot_service import list_slots, get_slot_details, get_floors_overview
from api.schemas import SlotResponse, FloorSummaryResponse

router = APIRouter(prefix="/api", tags=["Slots"])


@router.get("/slots", response_model=List[SlotResponse])
def get_slots(
    floor: Optional[int] = Query(None, ge=1, le=4, description="Filter by floor (1-4)"),
    status: Optional[str] = Query(None, description="Filter by status (available, occupied, reserved)"),
    vehicle_type: Optional[str] = Query(None, description="Filter by vehicle type (car, bike, suv)"),
    is_ev: Optional[int] = Query(None, ge=0, le=1, description="Filter by EV capability (1 or 0)"),
    is_disabled_friendly: Optional[int] = Query(None, ge=0, le=1, description="Filter by accessibility (1 or 0)"),
    search: Optional[str] = Query(None, description="Search by slot number"),
):
    """List all parking slots matching optional search filters."""
    with get_db() as conn:
        slots = list_slots(
            conn,
            floor=floor,
            status=status,
            vehicle_type=vehicle_type,
            is_ev=is_ev,
            is_disabled_friendly=is_disabled_friendly,
            search=search,
        )
        return slots


@router.get("/slots/{slot_id}", response_model=SlotResponse)
def get_single_slot(slot_id: int):
    """Retrieve details for a single parking slot by ID."""
    with get_db() as conn:
        slot = get_slot_details(conn, slot_id)
        if not slot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Slot with ID {slot_id} does not exist."
            )
        return slot


@router.get("/floors", response_model=List[FloorSummaryResponse])
def get_floors():
    """Retrieve floor-wise summary metrics and occupancy percentages."""
    with get_db() as conn:
        return get_floors_overview(conn)
