from pytest_bdd import when, then
import requests

BASE_URL = "http://localhost:8000"

# ---------------------------
# WHEN
# ---------------------------

@when("the availability is queried")
def query_availability(show_id, context):
    response = requests.get(
        f"{BASE_URL}/shows/{show_id}/availability"
    )
    assert response.status_code == 200
    context["availability"] = response.json()


# ---------------------------
# THEN
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
