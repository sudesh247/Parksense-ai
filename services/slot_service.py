"""
Service logic for managing parking slots and floor overviews.
"""

import sqlite3
from typing import List, Dict, Any, Optional
from database.queries import (
    get_all_slots,
    get_slot_by_id,
    get_floors_summary,
)
from utils.helpers import calculate_occupancy_percentage


def list_slots(
    conn: sqlite3.Connection,
    floor: Optional[int] = None,
    status: Optional[str] = None,
    vehicle_type: Optional[str] = None,
    is_ev: Optional[int] = None,
    is_disabled_friendly: Optional[int] = None,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieve slots with optional filters."""
    return get_all_slots(
        conn,
        floor=floor,
        status=status,
        vehicle_type=vehicle_type,
        is_ev=is_ev,
        is_disabled_friendly=is_disabled_friendly,
        search=search,
    )


def get_slot_details(conn: sqlite3.Connection, slot_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve details for a single slot by ID."""
    return get_slot_by_id(conn, slot_id)


def get_floors_overview(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Retrieve floor-wise summaries enriched with occupancy percentages."""
    floors_data = get_floors_summary(conn)
    result = []
    for f in floors_data:
        tot = f["total_slots"]
        occ = f["occupied_slots"]
        occ_pct = calculate_occupancy_percentage(occ, tot)
        result.append({
            "floor": f["floor"],
            "total_slots": tot,
            "available_slots": f["available_slots"],
            "occupied_slots": occ,
            "reserved_slots": f["reserved_slots"],
            "occupancy_percentage": occ_pct,
        })
    return result
