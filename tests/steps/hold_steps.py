from pytest_bdd import given, when, then, scenarios
import requests
import time

scenarios("../features/seat_hold.feature")


@given("3 seats are held with a valid expiry")
def hold_3_seats(show_id, context):
    resp = requests.post(
        f"http://localhost:8000/shows/{show_id}/hold",
        json={"seat_count": 3, "hold_duration_seconds": 300},
    )
    context["hold_id"] = resp.json()["hold_id"]


@given("4 seats are held but all holds are expired")
def expired_hold(show_id, context):
    resp = requests.post(
        f"http://localhost:8000/shows/{show_id}/hold",
        json={"seat_count": 4, "hold_duration_seconds": 1},
    )
    context["hold_id"] = resp.json()["hold_id"]
    time.sleep(2)


@when("a hold is requested for 3 seats with expiry of 5 minutes")
def request_hold(show_id, context):
    resp = requests.post(
        f"http://localhost:8000/shows/{show_id}/hold",
        json={"seat_count": 3, "hold_duration_seconds": 300},
    )
    context["response"] = resp


@then("the hold should be created successfully")
def hold_created(context):
    assert context["response"].status_code == 200
    assert "hold_id" in context["response"].json()
