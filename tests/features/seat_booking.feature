Feature: Seat Booking (Final Confirmation)

  Booking converts a valid temporary hold into a final,
  irreversible seat reservation. Booking must be atomic,
  idempotent, and safe under retries and failures.

  Background:
    Given a show with 10 seats exists

  Scenario: Successfully book seats from a valid hold
    Given a hold exists for 3 seats with valid expiry
    When the hold is confirmed for booking
    Then the booking should succeed
    And booked seats should be 3
    And held seats should be 0
    And available seats should be 7

  Scenario: Cannot book seats without a hold
    When a booking is attempted without a hold
    Then the booking should fail
    And booked seats should be 0
    And available seats should be 10

  Scenario: Cannot book seats from an expired hold
    Given a hold exists for 4 seats but all holds are expired
    When the hold is confirmed for booking
    Then the booking should fail
    And booked seats should be 0
    And available seats should be 10

  Scenario: Booking is irreversible
    Given a hold exists for 2 seats with valid expiry
    And the hold is confirmed for booking
    When availability is queried
    Then booked seats should be 2
    And available seats should be 8

  Scenario: Booking confirmation is idempotent
    Given a hold exists for 3 seats with valid expiry
    And the hold is confirmed for booking
    When the same booking confirmation is retried
    Then the booking should not create additional bookings
    And booked seats should be 3
    And available seats should be 7

  Scenario: Partial booking must not occur
    Given a hold exists for 5 seats with valid expiry
    When the booking operation fails midway
    Then no seats should be booked
    And held seats should still be 5
    And available seats should be 5

  Scenario: Booking survives response loss
    Given a hold exists for 4 seats with valid expiry
    When the hold is confirmed for booking
    And the client does not receive the response
    And the client retries booking confirmation
    Then booked seats should be 4
    And available seats should be 6

  Scenario: Booking survives system restart
    Given a hold exists for 3 seats with valid expiry
    And the hold is confirmed for booking
    And the system restarts
    When availability is queried
    Then booked seats should be 3
    And available seats should be 7
