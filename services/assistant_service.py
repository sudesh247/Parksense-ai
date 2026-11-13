"""
Assistant orchestration service managing intent routing, SQL execution, RAG synthesis, and graceful fallback.
"""

import sqlite3
import re
from typing import Dict, Any
from services.intent_router import classify_intent
from services.analytics_service import compute_dashboard_statistics
from database.queries import get_all_slots
from rag.rag_engine import answer_policy_question
from rag.llm_provider import get_llm, is_ollama_available
from rag.prompts import LIVE_DATA_PROMPT
from utils.helpers import get_current_iso_timestamp
from utils.logger import logger


def execute_live_data_query(conn: sqlite3.Connection, question: str, action_key: str) -> Dict[str, Any]:
    """Execute SQL query corresponding to the action key and return structured text & metadata."""
    q_lower = question.lower()

    if action_key == "AVAILABLE_SLOTS":
        slots = get_all_slots(conn, status="available")
        summary = f"Total Available Slots: {len(slots)}\n"
        by_floor = {}
        for s in slots:
            by_floor.setdefault(s["floor"], []).append(s["slot_number"])
        for flr in sorted(by_floor.keys()):
            summary += f"Floor {flr}: {', '.join(by_floor[flr][:8])} ({len(by_floor[flr])} available)\n"
        return {"raw_text": summary, "data": slots}

    elif action_key == "SLOTS_ON_FLOOR":
        match = re.search(r"floor\s+([1-4])", q_lower)
        flr = int(match.group(1)) if match else 1
        slots = get_all_slots(conn, floor=flr)
        avail = [s["slot_number"] for s in slots if s["status"] == "available"]
        occ = [s["slot_number"] for s in slots if s["status"] == "occupied"]
        res = [s["slot_number"] for s in slots if s["status"] == "reserved"]
        summary = (
            f"Floor {flr} Summary:\n"
            f"- Total Slots: {len(slots)}\n"
            f"- Available ({len(avail)}): {', '.join(avail[:10]) if avail else 'None'}\n"
            f"- Occupied ({len(occ)}): {', '.join(occ[:10]) if occ else 'None'}\n"
            f"- Reserved ({len(res)}): {', '.join(res[:10]) if res else 'None'}"
        )
        return {"raw_text": summary, "data": slots}

    elif action_key == "EV_SLOTS":
        slots = get_all_slots(conn, is_ev=1)
        avail = [s["slot_number"] for s in slots if s["status"] == "available"]
        occ = [s["slot_number"] for s in slots if s["status"] == "occupied"]
        summary = (
            f"EV Charging Slots Overview:\n"
            f"- Total EV Slots: {len(slots)}\n"
            f"- Currently Available ({len(avail)}): {', '.join(avail) if avail else 'None'}\n"
            f"- Currently Occupied ({len(occ)}): {', '.join(occ) if occ else 'None'}"
        )
        return {"raw_text": summary, "data": slots}

    elif action_key == "DISABLED_SLOTS":
        slots = get_all_slots(conn, is_disabled_friendly=1)
        avail = [s["slot_number"] for s in slots if s["status"] == "available"]
        summary = (
            f"Accessible / Disabled Parking Bays:\n"
            f"- Total Accessible Bays: {len(slots)}\n"
            f"- Available Bays ({len(avail)}): {', '.join(avail) if avail else 'None'}"
        )
        return {"raw_text": summary, "data": slots}

    elif action_key == "RESERVED_SLOTS":
        slots = get_all_slots(conn, is_reserved=1)
        summary = (
            f"Reserved Parking Slots:\n"
            f"- Total Designated Reserved Slots: {len(slots)}\n"
            f"- Slot Numbers: {', '.join([s['slot_number'] for s in slots])}"
        )
        return {"raw_text": summary, "data": slots}

    elif action_key == "TODAY_REVENUE":
        stats = compute_dashboard_statistics(conn)
        summary = (
            f"Today's Financial Summary:\n"
            f"- Today's Revenue: ₹{stats['today_revenue']:.2f}\n"
            f"- This Week's Revenue: ₹{stats['this_week_revenue']:.2f}\n"
            f"- Average Ticket Value: ₹{stats['average_ticket_value']:.2f}\n"
            f"- Today's Completed Bookings: {stats['today_bookings_count']}"
        )
        return {"raw_text": summary, "data": stats}

    elif action_key in ("OCCUPANCY_STATS", "HIGHEST_OCCUPANCY"):
        stats = compute_dashboard_statistics(conn)
        floors = stats["occupancy_by_floor"]
        highest = max(floors, key=lambda x: x["occupancy_percentage"]) if floors else None
        summary = (
            f"Facility Occupancy Statistics:\n"
            f"- Overall Facility Occupancy: {stats['overall_occupancy_percentage']}%\n"
            f"- Occupied Bays: {stats['occupied_slots']} / {stats['total_slots']}\n"
            f"- Available Bays: {stats['available_slots']}\n"
            f"- Floor with Highest Occupancy: Floor {highest['floor']} ({highest['occupancy_percentage']}%)" if highest else ""
        )
        return {"raw_text": summary, "data": stats}

    elif action_key in ("VEHICLE_MOVEMENT", "ACTIVE_VEHICLES"):
        stats = compute_dashboard_statistics(conn)
        summary = (
            f"Vehicle Movement & Activity Today:\n"
            f"- Currently Active Parked Vehicles: {stats['currently_active_vehicles']}\n"
            f"- Total Entries/Bookings Today: {stats['today_bookings_count']}"
        )
        return {"raw_text": summary, "data": stats}

    else:
        # Default fallback query
        slots = get_all_slots(conn)
        summary = f"Total Slots in Facility: {len(slots)}"
        return {"raw_text": summary, "data": slots}


def handle_assistant_question(conn: sqlite3.Connection, question: str) -> Dict[str, Any]:
    """
    Process assistant chat request through router:
    Type A (LIVE_DATA) -> SQL execution -> LLM format (or fallback template)
    Type B (POLICY) -> RAG retrieval -> LLM answer (or fallback template)
    Type C (OUT_OF_SCOPE) -> Refusal response
    """
    intent_type, action_key = classify_intent(question)
    timestamp = get_current_iso_timestamp()

    # Case 1: Out of Scope
    if intent_type == "OUT_OF_SCOPE":
        return {
            "answer": (
                "I am ParkSense AI, your dedicated smart parking assistant. "
                "I can answer questions regarding live slot availability, floor occupancy, today's revenue, "
                "parking tariffs, overstay rules, and EV charging guidelines. "
                "I cannot answer questions unrelated to parking operations."
            ),
            "intent": "OUT_OF_SCOPE",
            "source": "system_refusal",
            "retrieved_docs": [],
            "timestamp": timestamp,
        }

    # Case 2: Live Data (SQL)
    if intent_type == "LIVE_DATA":
        sql_res = execute_live_data_query(conn, question, action_key)
        raw_sql_text = sql_res["raw_text"]

        if is_ollama_available():
            try:
                llm = get_llm()
                if llm:
                    prompt = LIVE_DATA_PROMPT.format(question=question, sql_data=raw_sql_text)
                    formatted_ans = llm.invoke(prompt)
                    return {
                        "answer": str(formatted_ans).strip(),
                        "intent": "LIVE_DATA",
                        "source": "live_database",
                        "retrieved_docs": ["database/parksense.db"],
                        "timestamp": timestamp,
                    }
            except Exception as e:
                logger.error(f"Ollama error on live data formatting: {e}")

        # Offline fallback for Live Data
        fallback_answer = f"📊 **Live Parking Facility Data:**\n\n{raw_sql_text}"
        return {
            "answer": fallback_answer,
            "intent": "LIVE_DATA",
            "source": "live_database",
            "retrieved_docs": ["database/parksense.db"],
            "timestamp": timestamp,
        }

    # Case 3: Policy RAG
    if intent_type == "POLICY":
        rag_res = answer_policy_question(question)
        return {
            "answer": rag_res["answer"],
            "intent": "POLICY",
            "source": "rag_knowledge_base",
            "retrieved_docs": rag_res["retrieved_docs"],
            "timestamp": timestamp,
        }

    # Fallback default
    return {
        "answer": "I could not process your request. Please try asking about available slots, floor rates, or parking rules.",
        "intent": "UNKNOWN",
        "source": "system",
        "retrieved_docs": [],
        "timestamp": timestamp,
    }
