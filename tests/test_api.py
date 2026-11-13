"""
Automated pytest suite verifying ParkSense AI REST endpoints and business logic.
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from database.seed import seed_database_if_empty
from utils.helpers import calculate_parking_fee, calculate_occupancy_percentage
from services.intent_router import classify_intent

# Ensure database is seeded for test execution
seed_database_if_empty()

client = TestClient(app)


def test_health_endpoint():
    """Verify GET /api/health status code and payload format."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "ollama_ready" in data
    assert "vector_index_ready" in data


def test_slots_list_and_filter():
    """Verify GET /api/slots and query filter capabilities."""
    response = client.get("/api/slots")
    assert response.status_code == 200
    slots = response.json()
    assert len(slots) == 60

    # Filter floor 1
    f1_resp = client.get("/api/slots?floor=1")
    assert f1_resp.status_code == 200
    assert all(s["floor"] == 1 for s in f1_resp.json())

    # Filter EV
    ev_resp = client.get("/api/slots?is_ev=1")
    assert ev_resp.status_code == 200
    assert all(s["is_ev"] == 1 for s in ev_resp.json())


def test_single_slot_and_404():
    """Verify GET /api/slots/{id} success and 404 missing slot."""
    response = client.get("/api/slots/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1

    not_found = client.get("/api/slots/9999")
    assert not_found.status_code == 404


def test_floors_endpoint():
    """Verify GET /api/floors returns 4 floor objects."""
    response = client.get("/api/floors")
    assert response.status_code == 200
    floors = response.json()
    assert len(floors) == 4


def test_statistics_endpoint():
    """Verify GET /api/statistics contains non-zero expected KPI fields."""
    response = client.get("/api/statistics")
    assert response.status_code == 200
    stats = response.json()
    assert stats["total_slots"] == 60
    assert stats["overall_occupancy_percentage"] >= 0
    assert "revenue_trend" in stats
    assert len(stats["revenue_trend"]) == 14
    assert "vehicle_movement" in stats
    assert len(stats["vehicle_movement"]) == 24


def test_booking_lifecycle():
    """Test full booking lifecycle: Create -> List -> Release -> Conflict handling."""
    # Find an available slot first
    slots = client.get("/api/slots?status=available").json()
    assert len(slots) > 0
    target_slot = slots[0]

    # 1. Create booking (201)
    payload = {
        "slot_id": target_slot["id"],
        "vehicle_number": "TEST-1234",
        "vehicle_type": target_slot["vehicle_type"],
        "driver_name": "Test Driver"
    }
    create_res = client.post("/api/bookings", json=payload)
    assert create_res.status_code == 201
    booking = create_res.json()
    assert booking["status"] == "active"
    booking_id = booking["id"]

    # 2. Attempt duplicate booking on same slot (409 Conflict)
    conflict_res = client.post("/api/bookings", json=payload)
    assert conflict_res.status_code == 409

    # 3. Release booking (200)
    release_res = client.put(f"/api/bookings/{booking_id}/release")
    assert release_res.status_code == 200
    released = release_res.json()
    assert released["status"] == "completed"
    assert released["amount"] >= target_slot["price_per_hour"]

    # 4. Attempt re-releasing completed booking (409 Conflict)
    re_release = client.put(f"/api/bookings/{booking_id}/release")
    assert re_release.status_code == 409


def test_chat_intent_router():
    """Verify intent router classification logic for Live Data, Policy RAG, and Out of Scope (English & Hinglish)."""
    assert classify_intent("Which parking slots are available?")[0] == "LIVE_DATA"
    assert classify_intent("Khali slots kitne hai?")[0] == "LIVE_DATA"
    assert classify_intent("Show today's parking revenue")[0] == "LIVE_DATA"
    assert classify_intent("Aaj ki kamai kitni hui?")[0] == "LIVE_DATA"
    assert classify_intent("What are today's parking charges?")[0] == "POLICY"
    assert classify_intent("Parking rates kya hai?")[0] == "POLICY"
    assert classify_intent("What happens if I overstay?")[0] == "POLICY"
    assert classify_intent("Overstay fine kitna hai?")[0] == "POLICY"
    assert classify_intent("Who won the 2024 election?")[0] == "OUT_OF_SCOPE"


def test_chat_endpoint_responses():
    """Verify POST /api/chat endpoint handling."""
    # Live data question
    res_a = client.post("/api/chat", json={"question": "Which slots are available?"})
    assert res_a.status_code == 200
    assert res_a.json()["intent"] == "LIVE_DATA"

    # Policy question
    res_b = client.post("/api/chat", json={"question": "What are the parking rules?"})
    assert res_b.status_code == 200
    assert res_b.json()["intent"] == "POLICY"

    # Out of scope question
    res_c = client.post("/api/chat", json={"question": "Who is the CEO of Google?"})
    assert res_c.status_code == 200
    assert res_c.json()["intent"] == "OUT_OF_SCOPE"
    assert res_c.json()["source"] == "system_refusal"


def test_billing_calculation_helper():
    """Verify ceiling and minimum 1-hour billing logic."""
    # 30 mins -> 1 hour
    fee_1 = calculate_parking_fee("2026-08-26T10:00:00Z", "2026-08-26T10:30:00Z", 40.0)
    assert fee_1 == 40.0

    # 1 hr 15 mins -> 2 hours
    fee_2 = calculate_parking_fee("2026-08-26T10:00:00Z", "2026-08-26T11:15:00Z", 40.0)
    assert fee_2 == 80.0
