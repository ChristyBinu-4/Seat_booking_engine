Feature: Seat Availability

  The system must always report correct seat availability
  regardless of concurrent holds, bookings, expiries, retries,
  or system restarts.

  Background:
    Given a show with 10 seats exists

  Scenario: All seats are available initially
    When the availability is queried
    Then available seats should be 10
    And held seats should be 0
    And booked seats should be 0

  Scenario: Seats become unavailable when held
    Given 3 seats are held with a valid expiry
    When the availability is queried
    Then available seats should be 7
    And held seats should be 3
    And booked seats should be 0

  Scenario: Expired held seats become available again
    Given 4 seats are held but all holds are expired
    When the availability is queried
    Then available seats should be 10
    And held seats should be 0
    And booked seats should be 0

  Scenario: Booked seats reduce availability permanently
    Given 2 seats are booked successfully
    When the availability is queried
    Then available seats should be 8
    And held seats should be 0
    And booked seats should be 2

  Scenario: Mixed seat states are reported correctly
    Given 3 seats are held with a valid expiry
    And 2 seats are booked successfully
    When the availability is queried
    Then available seats should be 5
    And held seats should be 3
    And booked seats should be 2

  Scenario: Expired holds do not affect availability even if rows exist
    Given 5 seats are held but all holds are expired
    And 1 seat is booked successfully
    When the availability is queried
    Then available seats should be 9
    And held seats should be 0
    And booked seats should be 1

  Scenario: Availability remains correct after system restart
    Given 3 seats are held with a valid expiry
    And 2 seats are booked successfully
    And the system restarts
    When the availability is queried
    Then available seats should be 5
    And held seats should be 3
    And booked seats should be 2
