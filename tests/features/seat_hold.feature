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

  Scenario: Holding seats reduces availability immediately
    Given a hold exists for 4 seats with valid expiry
    When the availability is queried
    Then available seats should be 6
    And held seats should be 4
    And booked seats should be 0

  Scenario: Cannot hold more seats than available
    Given a hold exists for 8 seats with valid expiry
    When a hold is requested for 3 seats with expiry of 5 minutes
    Then the hold request should fail
    And available seats should be 2
    And held seats should be 8
    And booked seats should be 0

  Scenario: Holds are exclusive per seat
    Given a hold exists for 5 seats with valid expiry
    When another hold is requested for 1 of the same seats
    Then the hold request should fail
    And held seats should still be 5

  Scenario: Expired holds do not block new holds
    Given a hold exists for 6 seats but all holds are expired
    When a hold is requested for 4 seats with expiry of 5 minutes
    Then the hold should be created successfully
    And held seats should be 4
    And available seats should be 6

  Scenario: Hold expiry automatically releases seats
    Given a hold exists for 3 seats with expiry of 1 second
    And the hold expires
    When the availability is queried
    Then held seats should be 0
    And available seats should be 10
    And booked seats should be 0

  Scenario: Holding seats is atomic
    When a hold is requested for 4 seats
    And the hold operation fails midway
    Then no seats should be held
    And available seats should be 10
