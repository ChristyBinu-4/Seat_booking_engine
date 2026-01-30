from pytest_bdd import given, when, then, scenarios
import requests

scenarios("../features/seat_availability.feature")


@given("a show with 10 seats exists")
def given_show_exists(show_id):
    return show_id


@when("the availability is queried")
def query_availability(show_id, context):
    response = requests.get(
        f"http://localhost:8000/shows/{show_id}/availability"
    )
    context["availability"] = response.json()


@then("available seats should be 10")
def available_10(context):
    assert context["availability"]["available"] == 10


@then("held seats should be 0")
def held_0(context):
    assert context["availability"]["held"] == 0


@then("booked seats should be 0")
def booked_0(context):
    assert context["availability"]["booked"] == 0
