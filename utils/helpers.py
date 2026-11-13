"""
Helper functions for ParkSense AI business logic.
"""

import math
from datetime import datetime, timezone


def get_current_iso_timestamp() -> str:
    """Return the current UTC timestamp formatted as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def calculate_parking_fee(entry_time_iso: str, exit_time_iso: str, price_per_hour: float) -> float:
    """
    Compute parking fee based on entry and exit ISO timestamps.
    Billing Rule: amount = ceil(duration_hours) * price_per_hour, minimum 1 hour.
    """
    entry_dt = datetime.fromisoformat(entry_time_iso.replace("Z", "+00:00"))
    exit_dt = datetime.fromisoformat(exit_time_iso.replace("Z", "+00:00"))

    duration_seconds = (exit_dt - entry_dt).total_seconds()
    if duration_seconds < 0:
        duration_seconds = 0

    duration_hours = duration_seconds / 3600.0
    billable_hours = math.ceil(duration_hours)
    if billable_hours < 1:
        billable_hours = 1

    return round(billable_hours * price_per_hour, 2)


def calculate_occupancy_percentage(occupied_count: int, total_count: int) -> float:
    """Calculate percentage occupancy rounded to 1 decimal place."""
    if total_count <= 0:
        return 0.0
    return round((occupied_count / total_count) * 100.0, 1)
