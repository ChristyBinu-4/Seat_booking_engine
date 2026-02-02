# Seat Booking Engine (Backend Only)

## Overview
This project implements the core seat-booking engine for a movie show.

---

## Problem We’re Solving
In real systems:
- Multiple users try to book the same seats at the same time
- Users abandon bookings midway
- Requests get retried
- Responses get lost
- Systems restart while operations are in progress

Despite all this, the system must **never sell more seats than exist**.

---

## Design Principles

### 1. Database Is the Single Source of Truth
- No in-memory state is trusted.
- Every decision (availability, holds, bookings) is derived directly from the database.
- If the process crashes or restarts, correctness is preserved.

### 2. Seat State Is Derived, Not Stored
A seat is never marked with a mutable “state” column.

Instead, its state is derived:

- **Available**
  - No active hold
  - No booking
- **Held**
  - A non-expired hold exists
- **Booked**
  - A booking exists

This avoids synchronization bugs and stale state.

### 3. Time-Bound Holds (No Background Cleanup)
- Seat holds expire automatically using timestamps.
- ❌ No cron job  
- ❌ No background worker  

Expired holds are simply ignored by queries.

### 4. Atomic, Idempotent Operations
All write operations are:
- **Atomic** → all or nothing
- **Idempotent** → safe to retry

This ensures safety under retries, response loss, and partial failures.

---

## Core Concepts

### Seat Hold (Temporary Reservation)
- A hold temporarily reserves seats
- Each seat in a hold has its own row
- Holds automatically expire
- A single `hold_id` may reference multiple seats

### Booking (Final Reservation)
- Booking converts a valid hold into a permanent reservation
- Bookings are irreversible
- Booking confirmation is idempotent

Retrying the same booking confirmation:
- Does not create duplicate bookings
- Returns the same booking result

---
- **Testing:** pytest + pytest-bdd
## Data Model (Simplified)
- **shows** – one movie show
- **seats** – all seats in a show
- **seat_holds** – temporary reservations (with expiry)
- **bookings** – confirmed bookings
- **booking_seats** – seats linked to bookings

Each table has a single responsibility and no duplicated meaning.

---

## Availability Logic
Availability is calculated on demand:
- Total seats
- Minus booked seats- **Testing:** pytest + pytest-bdd
- Minus currently active (non-expired) holds

Expired holds automatically stop affecting availability.

This ensures availability is always correct — even after restarts.

---

## Handling Concurrency
Concurrency is handled at the database level using:
- `SELECT … FOR UPDATE SKIP LOCKED`
- Proper transaction boundaries

This guarantees:
- No two users can hold the same seat
- No overbooking is possible

---

## Testing Strategy (BDD)
The system is tested using **Behavior-Driven Development** with `pytest-bdd`.

### Why BDD?
Instead of testing internal functions, we test observable behavior:
- What happens when a user holds seats?
- What happens when holds expire?
- What happens when bookings are retried?

### Minimal but Sufficient Scenarios
Only essential invariants are tested:
- **Availability**
  - Fresh system shows all seats available
- **Hold**
  - Holding seats reduces availability
  - Expired holds release seats automatically
- **Booking**
  - Valid holds can be booked
  - Expired holds cannot be booked
  - Booking confirmation is idempotent

Each scenario proves a fundamental correctness rule.

---

## Technology Stack
- **Language:** Python 3.12
- **API:** FastAPI
- **Database:** PostgreSQL
- **DB Driver:** psycopg2
- **Containerization:** Docker & docker-compose (optional)

---

## Running the Project (Locally)

### Start the API
```bash
uvicorn app.main:app --reload
```
### Running Docker
```
try to run docker-compose down-v 
```
before building docker image, otherwise the data will persist in db>
```
docker-compose down -v && docker-compose up --build
```

### Run Tests
```bash
pytest -v
```

---

## Why This Approach Works
- No hidden state
- No race conditions
- No cleanup jobs
- No reliance on timing assumptions
- Safe under retries and crashes

The system stays correct because the database enforces correctness, not application logic.

---

## Final Note
This project is intentionally small, focused, and opinionated.

It demonstrates how to design a reliable seat-booking engine by:
- Reducing moving parts
- Trusting the database
- Testing only what truly matters

That’s how real systems stay correct at scale.