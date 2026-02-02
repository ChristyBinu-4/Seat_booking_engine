from pytest_bdd import given, when, then
import requests
import time

BASE_URL = "http://localhost:8000"


# ---------------------------
# Helpers
# ---------------------------

def get_availability(show_id):
    resp = requests.get(f"{BASE_URL}/shows/{show_id}/availability")
    assert resp.status_code == 200
    return resp.json()


# ---------------------------
# GIVEN
# ---------------------------

@given("a hold exists for 3 seats with valid expiry")
def hold_3_seats(show_id, context):
    resp = requests.post(
        f"{BASE_URL}/shows/{show_id}/hold",
        json={"seat_count": 3, "hold_duration_seconds": 300},
    )
    assert resp.status_code == 200
    context["hold_id"] = resp.json()["hold_id"]


@given("a hold exists for 3 seats with valid expiry")
def hold_3_seats_valid(show_id, context):
    resp = requests.post(
        f"{BASE_URL}/shows/{show_id}/hold",
        json={"seat_count": 3, "hold_duration_seconds": 300},
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


# ---------------------------
# WHEN
# ---------------------------

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
# THEN
# ---------------------------

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
    availability = get_availability(context["show_id"])
    assert availability["booked"] == 3


@then("booked seats should be 0")
def assert_booked_0(context):
    availability = get_availability(context["show_id"])
    assert availability["booked"] == 0


@then("held seats should be 0")
def assert_held_zero(context):
    availability = get_availability(context["show_id"])
    assert availability["held"] == 0


@then("available seats should be 7")
def assert_available_7(context):
    availability = get_availability(context["show_id"])
    assert availability["available"] == 7


@then("available seats should be 10")
def assert_available_10(context):
    availability = get_availability(context["show_id"])
    assert availability["available"] == 10
