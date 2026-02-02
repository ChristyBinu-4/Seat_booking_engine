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

@given("a hold exists for 3 seats with expiry of 1 second")
def short_hold(show_id, context):
    resp = requests.post(
        f"{BASE_URL}/shows/{show_id}/hold",
        json={"seat_count": 3, "hold_duration_seconds": 1},
    )
    assert resp.status_code == 200
    context["hold_id"] = resp.json()["hold_id"]


@given("the hold expires")
def wait_for_expiry():
    time.sleep(2)


# ---------------------------
# WHEN
# ---------------------------

@when("a hold is requested for 3 seats with expiry of 5 minutes")
def request_hold(show_id, context):
    resp = requests.post(
        f"{BASE_URL}/shows/{show_id}/hold",
        json={"seat_count": 3, "hold_duration_seconds": 300},
    )
    context["response"] = resp
    if resp.status_code == 200:
        context["hold_id"] = resp.json()["hold_id"]


@when("the availability is queried")
def query_availability(show_id, context):
    context["availability"] = get_availability(show_id)


# ---------------------------
# THEN
# ---------------------------

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


@then("booked seats should be 0")
def assert_booked(context):
    assert context["availability"]["booked"] == 0
