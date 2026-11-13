"""
Pydantic schemas for API request and response validation.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SlotResponse(BaseModel):
    id: int
    slot_number: str
    floor: int
    status: str
    price_per_hour: float
    vehicle_type: str
    is_ev: int
    near_exit: int
    is_reserved: int
    is_disabled_friendly: int


class FloorSummaryResponse(BaseModel):
    floor: int
    total_slots: int
    available_slots: int
    occupied_slots: int
    reserved_slots: int
    occupancy_percentage: float


class BookingCreateRequest(BaseModel):
    slot_id: int = Field(..., description="ID of the parking slot to book", json_schema_extra={"example": 1})
    vehicle_number: str = Field(..., description="Vehicle registration plate number", json_schema_extra={"example": "MH02-AB1234"})
    vehicle_type: str = Field(..., description="Vehicle category: car, bike, suv", json_schema_extra={"example": "car"})
    driver_name: Optional[str] = Field(None, description="Optional driver full name", json_schema_extra={"example": "Aarav Sharma"})


class BookingResponse(BaseModel):
    id: int
    slot_id: int
    slot_number: str
    floor: int
    price_per_hour: float
    vehicle_number: str
    vehicle_type: str
    driver_name: Optional[str] = None
    entry_time: str
    exit_time: Optional[str] = None
    amount: Optional[float] = None
    status: str


class EVDisabledCounts(BaseModel):
    total: int
    available: int


class RevenueTrendItem(BaseModel):
    date: str
    revenue: float


class VehicleMovementItem(BaseModel):
    hour: int
    label: str
    entries: int
    exits: int


class StatisticsResponse(BaseModel):
    overall_occupancy_percentage: float
    total_slots: int
    available_slots: int
    occupied_slots: int
    reserved_slots: int
    today_revenue: float
    this_week_revenue: float
    average_ticket_value: float
    today_bookings_count: int
    currently_active_vehicles: int
    ev_slots: EVDisabledCounts
    disabled_slots: EVDisabledCounts
    occupancy_by_floor: List[FloorSummaryResponse]
    revenue_trend: List[RevenueTrendItem]
    vehicle_movement: List[VehicleMovementItem]


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User question for the AI assistant", json_schema_extra={"example": "Which slots are available?"})


class ChatResponse(BaseModel):
    answer: str
    intent: str
    source: str
    retrieved_docs: List[str]
    timestamp: str


class HealthResponse(BaseModel):
    status: str
    ollama_ready: bool
    vector_index_ready: bool
