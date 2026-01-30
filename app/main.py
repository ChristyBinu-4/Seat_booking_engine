from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import os

from app.engine import SeatBookingEngine

# -------------------------
# App & DB setup
# -------------------------

app = FastAPI(title="Seat Booking Engine")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@db:5432/postgres"
)

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = False

engine = SeatBookingEngine(conn)

# -------------------------
# Request / Response models
# -------------------------

class HoldRequest(BaseModel):
    seat_count: int
    hold_duration_seconds: int


class HoldResponse(BaseModel):
    hold_id: str


class BookingResponse(BaseModel):
    booking_id: str


class AvailabilityResponse(BaseModel):
    available: int
    held: int
    booked: int


# -------------------------
# Routes
# -------------------------

@app.get(
    "/shows/{show_id}/availability",
    response_model=AvailabilityResponse
)
def get_availability(show_id: str):
    try:
        return engine.get_availability(show_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post(
    "/shows/{show_id}/hold",
    response_model=HoldResponse
)
def hold_seats(show_id: str, request: HoldRequest):
    try:
        hold_id = engine.hold_seats(
            show_id=show_id,
            seat_count=request.seat_count,
            hold_duration_seconds=request.hold_duration_seconds,
        )
        return {"hold_id": hold_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post(
    "/holds/{hold_id}/confirm",
    response_model=BookingResponse
)
def confirm_booking(hold_id: str):
    try:
        booking_id = engine.confirm_booking(hold_id)
        return {"booking_id": booking_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
