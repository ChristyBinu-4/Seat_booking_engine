from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import psycopg2
import os

from app.engine import SeatBookingEngine

# -------------------------
# App setup
# -------------------------

app = FastAPI(title="Seat Booking Engine")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/postgres"
)

# -------------------------
# Lifespan events
# -------------------------

@app.on_event("startup")
def startup():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    app.state.conn = conn
    app.state.engine = SeatBookingEngine(conn)


@app.on_event("shutdown")
def shutdown():
    app.state.conn.close()

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
def get_availability(show_id: str, request: Request):
    try:
        return request.app.state.engine.get_availability(show_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post(
    "/shows/{show_id}/hold",
    response_model=HoldResponse
)
def hold_seats(show_id: str, request: HoldRequest, req: Request):
    try:
        hold_id = req.app.state.engine.hold_seats(
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
def confirm_booking(hold_id: str, request: Request):
    try:
        booking_id = request.app.state.engine.confirm_booking(hold_id)
        return {"booking_id": booking_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
