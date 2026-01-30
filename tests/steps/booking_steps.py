from pytest_bdd import given, when, then, scenarios
import requests

scenarios("../features/seat_booking.feature")


@given("a hold exists for 3 seats with valid expiry")
def hold_for_booking(show_id, context):
    resp = requests.post(
        f"http://localhost:8000/shows/{show_id}/hold",
        json={"seat_count": 3, "hold_duration_seconds": 300},
    )
    context["hold_id"] = resp.json()["hold_id"]


@when("the hold is confirmed for booking")
def confirm_booking(context):
    resp = requests.post(
        f"http://localhost:8000/holds/{context['hold_id']}/confirm"
    )
    context["booking_response"] = resp


@then("the booking should succeed")
def booking_success(context):
    assert context["booking_response"].status_code == 200
    assert "booking_id" in context["booking_response"].json()
