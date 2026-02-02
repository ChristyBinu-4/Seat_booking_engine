Feature: Seat Availability

  The system must always report correct seat availability
  based on the current persisted seat state.

  Background:
    Given a show with 10 seats exists

  Scenario: All seats are available initially
    When the availability is queried
    Then available seats should be 10
    And held seats should be 0
    And booked seats should be 0
