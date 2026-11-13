"""
Pandas and NumPy analytics processing service for dashboard KPIs and trends.
"""

import sqlite3
from datetime import datetime, timedelta, timezone
import pandas as pd
import numpy as np
from typing import Dict, Any, List

from database.queries import get_raw_slots_for_analytics, get_raw_bookings_for_analytics
from utils.helpers import calculate_occupancy_percentage


def compute_dashboard_statistics(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Compute overall facility metrics, revenue trends, and hourly vehicle movement using Pandas/NumPy."""
    raw_slots = get_raw_slots_for_analytics(conn)
    raw_bookings = get_raw_bookings_for_analytics(conn)

    df_slots = pd.DataFrame(raw_slots) if raw_slots else pd.DataFrame(columns=[
        "id", "slot_number", "floor", "status", "price_per_hour", "vehicle_type", "is_ev", "near_exit", "is_reserved", "is_disabled_friendly"
    ])

    df_bookings = pd.DataFrame(raw_bookings) if raw_bookings else pd.DataFrame(columns=[
        "id", "slot_id", "vehicle_number", "vehicle_type", "driver_name", "entry_time", "exit_time", "amount", "status", "floor", "price_per_hour"
    ])

    # Slot level KPI metrics
    total_slots = int(len(df_slots))
    available_slots = int((df_slots["status"] == "available").sum()) if not df_slots.empty else 0
    occupied_slots = int((df_slots["status"] == "occupied").sum()) if not df_slots.empty else 0
    reserved_slots = int((df_slots["status"] == "reserved").sum()) if not df_slots.empty else 0

    overall_occupancy_pct = calculate_occupancy_percentage(occupied_slots, total_slots)

    # EV and Disabled slot counts
    ev_total = int(df_slots["is_ev"].sum()) if not df_slots.empty else 0
    ev_available = int(((df_slots["is_ev"] == 1) & (df_slots["status"] == "available")).sum()) if not df_slots.empty else 0

    disabled_total = int(df_slots["is_disabled_friendly"].sum()) if not df_slots.empty else 0
    disabled_available = int(((df_slots["is_disabled_friendly"] == 1) & (df_slots["status"] == "available")).sum()) if not df_slots.empty else 0

    # Bookings temporal calculations
    now_utc = datetime.now(timezone.utc)
    today_start = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)

    today_revenue = 0.0
    week_revenue = 0.0
    avg_ticket_value = 0.0
    today_bookings_count = 0
    currently_active_vehicles = 0

    revenue_trend: List[Dict[str, Any]] = []
    vehicle_movement: List[Dict[str, Any]] = []
    occupancy_by_floor: List[Dict[str, Any]] = []

    if not df_bookings.empty:
        # Convert entry_time and exit_time to datetime with flexible ISO8601 parsing
        df_bookings["entry_dt"] = pd.to_datetime(df_bookings["entry_time"], format="ISO8601", utc=True)
        df_bookings["exit_dt"] = pd.to_datetime(df_bookings["exit_time"], format="ISO8601", utc=True)

        currently_active_vehicles = int((df_bookings["status"] == "active").sum())

        # Today's bookings mask
        today_mask = df_bookings["entry_dt"] >= today_start
        today_bookings_count = int(today_mask.sum())

        # Revenue calculations (completed bookings with non-null amount)
        completed_bookings = df_bookings[df_bookings["status"] == "completed"].copy()
        if not completed_bookings.empty:
            today_completed = completed_bookings[completed_bookings["entry_dt"] >= today_start]
            today_revenue = float(today_completed["amount"].sum()) if not today_completed.empty else 0.0

            week_completed = completed_bookings[completed_bookings["entry_dt"] >= week_start]
            week_revenue = float(week_completed["amount"].sum()) if not week_completed.empty else 0.0

            avg_ticket_value = float(completed_bookings["amount"].mean()) if not completed_bookings.empty else 0.0

        # Revenue Trend: Last 14 days
        dates_14 = [today_start.date() - timedelta(days=i) for i in range(13, -1, -1)]
        revenue_map = {}
        if not completed_bookings.empty:
            completed_bookings["entry_date"] = completed_bookings["entry_dt"].dt.date
            daily_rev = completed_bookings.groupby("entry_date")["amount"].sum().to_dict()
            revenue_map = daily_rev

        for d in dates_14:
            revenue_trend.append({
                "date": d.strftime("%Y-%m-%d"),
                "revenue": float(revenue_map.get(d, 0.0))
            })

        # Vehicle Movement Today: Entry and Exit bucketed by hour (0 to 23)
        today_entries = df_bookings[today_mask]
        today_exits = df_bookings[(df_bookings["exit_dt"].notnull()) & (df_bookings["exit_dt"] >= today_start)]

        entry_counts = today_entries["entry_dt"].dt.hour.value_counts().to_dict() if not today_entries.empty else {}
        exit_counts = today_exits["exit_dt"].dt.hour.value_counts().to_dict() if not today_exits.empty else {}

        for hr in range(24):
            vehicle_movement.append({
                "hour": hr,
                "label": f"{hr:02d}:00",
                "entries": int(entry_counts.get(hr, 0)),
                "exits": int(exit_counts.get(hr, 0)),
            })
    else:
        # Fallback empty structures if no bookings
        dates_14 = [today_start.date() - timedelta(days=i) for i in range(13, -1, -1)]
        revenue_trend = [{"date": d.strftime("%Y-%m-%d"), "revenue": 0.0} for d in dates_14]
        vehicle_movement = [{"hour": hr, "label": f"{hr:02d}:00", "entries": 0, "exits": 0} for hr in range(24)]

    # Occupancy by Floor
    if not df_slots.empty:
        floor_grp = df_slots.groupby("floor")
        for flr, group in floor_grp:
            f_total = len(group)
            f_occupied = int((group["status"] == "occupied").sum())
            f_reserved = int((group["status"] == "reserved").sum())
            f_pct = calculate_occupancy_percentage(f_occupied, f_total)
            occupancy_by_floor.append({
                "floor": int(flr),
                "total_slots": f_total,
                "occupied_slots": f_occupied,
                "reserved_slots": f_reserved,
                "available_slots": int((group["status"] == "available").sum()),
                "occupancy_percentage": f_pct,
            })

    return {
        "overall_occupancy_percentage": overall_occupancy_pct,
        "total_slots": total_slots,
        "available_slots": available_slots,
        "occupied_slots": occupied_slots,
        "reserved_slots": reserved_slots,
        "today_revenue": round(today_revenue, 2),
        "this_week_revenue": round(week_revenue, 2),
        "average_ticket_value": round(avg_ticket_value, 2),
        "today_bookings_count": today_bookings_count,
        "currently_active_vehicles": currently_active_vehicles,
        "ev_slots": {"total": ev_total, "available": ev_available},
        "disabled_slots": {"total": disabled_total, "available": disabled_available},
        "occupancy_by_floor": occupancy_by_floor,
        "revenue_trend": revenue_trend,
        "vehicle_movement": vehicle_movement,
    }
