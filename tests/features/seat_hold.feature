Feature: Seat Hold (Temporary Reservation)

  Seats can be temporarily held to prevent other users
  from booking them while a booking is in progress.
  Holds are time-bound and expire automatically.

  Background:
    Given a show with 10 seats exists

  Scenario: Successfully hold seats when enough seats are available
    When a hold is requested for 3 seats with expiry of 5 minutes
    Then the hold should be created successfully
    And held seats should be 3
    And available seats should be 7
    And booked seats should be 0

  Scenario: Hold expiry automatically releases seats
    Given a hold exists for 3 seats with expiry of 1 second
    And the hold expires
    When the availability is queried
    Then held seats should be 0
    And available seats should be 10
    And booked seats should be 0
