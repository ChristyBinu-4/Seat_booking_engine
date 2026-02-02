import pytest
from pytest_bdd import given, when, then, parsers
import uuid
import requests
import time
import psycopg2
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/postgres"
)

# For Docker environment, use the container name as host
if os.getenv("DOCKER_ENV"):
    DATABASE_URL = "postgresql://postgres:postgres@seat_booking_db:5432/postgres"

BASE_URL = os.getenv(
    "BASE_URL",
    "http://localhost:8000"
)

# For Docker environment, use the container name as host
if os.getenv("DOCKER_ENV"):
    BASE_URL = "http://seat_booking_api:8000"

# ---------------------------
# Fixtures
# ---------------------------

@pytest.fixture
def db_conn():
    """Database connection fixture for tests"""
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    yield conn
    conn.close()

@pytest.fixture
def context():
    """Context dictionary to share data between steps"""
    return {}

@pytest.fixture(autouse=True)
def setup_test_database(db_conn):
    """Setup test database before each test"""
    with db_conn:
        with db_conn.cursor() as cur:
            # Clean up existing data (in reverse order of dependencies)
            cur.execute("DELETE FROM booking_seats")
            cur.execute("DELETE FROM bookings")
            cur.execute("DELETE FROM seat_holds")
            cur.execute("DELETE FROM seats")
            cur.execute("DELETE FROM shows")
    
    yield
    
    with db_conn:
        with db_conn.cursor() as cur:
            # Clean up after test (in reverse order of dependencies)
            cur.execute("DELETE FROM booking_seats")
            cur.execute("DELETE FROM bookings")
            cur.execute("DELETE FROM seat_holds")
            cur.execute("DELETE FROM seats")
            cur.execute("DELETE FROM shows")

# ---------------------------
# GIVEN steps
# ---------------------------

@given("a show with 10 seats exists", target_fixture="show_id")
def show_with_10_seats(db_conn):
    # Use SERIAL for show_id since the schema defines it as BIGSERIAL
    with db_conn:
        with db_conn.cursor() as cur:
            # Insert show and get the generated ID
            cur.execute("INSERT INTO shows (total_seats) VALUES (%s) RETURNING show_id", (10,))
            show_id = cur.fetchone()[0]
            
            # Insert seats for this show
            for i in range(1, 11):
                cur.execute(
                    """
                    INSERT INTO seats (show_id, seat_number)
                    VALUES (%s, %s)
                    """,
                    (show_id, i),
                )

    return show_id

@given("a hold exists for 3 seats with valid expiry")
def hold_3_seats_valid(show_id, context):
    resp = requests.post(
        f"{BASE_URL}/shows/{show_id}/hold",
        json={"seat_count": 3, "hold_duration_seconds": 300},
    )
    assert resp.status_code == 200
    context["hold_id"] = resp.json()["hold_id"]

@given("a hold exists for 3 seats with expiry of 1 second")
def short_hold(show_id, context):
    resp = requests.post(
        f"{BASE_URL}/shows/{show_id}/hold",
        json={"seat_count": 3, "hold_duration_seconds": 1},
    )
    assert resp.status_code == 200
    context["hold_id"] = resp.json()["hold_id"]

@given("a hold exists for 4 seats but all holds are expired")
def expired_hold_4_seats(show_id, context):
    resp = requests.post(
        f"{BASE_URL}/shows/{show_id}/hold",
        json={"seat_count": 4, "hold_duration_seconds": 1},
    )
    assert resp.status_code == 200
    context["hold_id"] = resp.json()["hold_id"]
    time.sleep(2)  # allow hold to expire

@given("the hold expires")
def wait_for_expiry():
    time.sleep(2)

# ---------------------------
# WHEN steps
# ---------------------------

@when("the availability is queried")
def query_availability(show_id, context):
    response = requests.get(
        f"{BASE_URL}/shows/{show_id}/availability"
    )
    assert response.status_code == 200
    context["availability"] = response.json()

@when("a hold is requested for 3 seats with expiry of 5 minutes")
def request_hold(show_id, context):
    resp = requests.post(
        f"{BASE_URL}/shows/{show_id}/hold",
        json={"seat_count": 3, "hold_duration_seconds": 300},
    )
    context["response"] = resp
    if resp.status_code == 200:
        context["hold_id"] = resp.json()["hold_id"]

@when("the hold is confirmed for booking")
def confirm_booking(show_id, context):
    resp = requests.post(
        f"{BASE_URL}/holds/{context['hold_id']}/confirm"
    )
    context["response"] = resp
    if resp.status_code == 200:
        context["booking_id"] = resp.json().get("booking_id")

@when("the same booking confirmation is retried")
def retry_booking(context):
    resp = requests.post(
        f"{BASE_URL}/holds/{context['hold_id']}/confirm"
    )
    context["retry_response"] = resp
    if resp.status_code == 200:
        context["retry_booking_id"] = resp.json().get("booking_id")

# ---------------------------
# THEN steps
# ---------------------------

@then("available seats should be 10")
def available_10(context):
    assert context["availability"]["available"] == 10

@then("held seats should be 0")
def held_0(context):
    assert context["availability"]["held"] == 0

@then("booked seats should be 0")
def booked_0(context):
    assert context["availability"]["booked"] == 0

@then("the hold should be created successfully")
def hold_created(context):
    assert context["response"].status_code == 200
    assert "hold_id" in context["response"].json()

@then("held seats should be 3")
def assert_held_3(context):
    assert context["availability"]["held"] == 3

@then("held seats should be 0")
def assert_held_0(context):
    assert context["availability"]["held"] == 0

@then("available seats should be 7")
def assert_available_7(context):
    assert context["availability"]["available"] == 7

@then("available seats should be 10")
def assert_available_10(context):
    assert context["availability"]["available"] == 10

@then("the booking should succeed")
def booking_succeeds(context):
    assert context["response"].status_code == 200
    assert "booking_id" in context["response"].json()

@then("the booking should fail")
def booking_fails(context):
    assert context["response"].status_code >= 400

@then("the booking should not create additional bookings")
def booking_idempotent(context):
    assert context["response"].status_code == 200
    assert context["retry_response"].status_code == 200
    assert context["booking_id"] == context["retry_booking_id"]

@then("booked seats should be 3")
def assert_booked_3(context):
    availability = requests.get(f"{BASE_URL}/shows/{context['show_id']}/availability")
    assert availability.status_code == 200
    assert availability.json()["booked"] == 3

@then("booked seats should be 0")
def assert_booked_0(context):
    availability = requests.get(f"{BASE_URL}/shows/{context['show_id']}/availability")
    assert availability.status_code == 200
    assert availability.json()["booked"] == 0

@then("held seats should be 0")
def assert_held_zero(context):
    availability = requests.get(f"{BASE_URL}/shows/{context['show_id']}/availability")
    assert availability.status_code == 200
    assert availability.json()["held"] == 0

@then("available seats should be 7")
def assert_available_7(context):
    availability = requests.get(f"{BASE_URL}/shows/{context['show_id']}/availability")
    assert availability.status_code == 200
    assert availability.json()["available"] == 7

@then("available seats should be 10")
def assert_available_10(context):
    availability = requests.get(f"{BASE_URL}/shows/{context['show_id']}/availability")
    assert availability.status_code == 200
    assert availability.json()["available"] == 10
