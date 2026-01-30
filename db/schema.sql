CREATE TABLE IF NOT EXISTS shows (
    show_id     BIGSERIAL PRIMARY KEY,
    total_seats INT NOT NULL CHECK (total_seats > 0),
    created_at  TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS seats (
    seat_id     BIGSERIAL PRIMARY KEY,
    show_id     BIGINT NOT NULL
        REFERENCES shows(show_id) ON DELETE CASCADE,
    seat_number INT NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT now(),
    UNIQUE (show_id, seat_number)
);

CREATE TABLE seat_holds (
    hold_id    UUID NOT NULL,
    show_id    BIGINT NOT NULL
        REFERENCES shows(show_id) ON DELETE CASCADE,
    seat_id    BIGINT NOT NULL
        REFERENCES seats(seat_id) ON DELETE CASCADE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now(),

    PRIMARY KEY (hold_id, seat_id),
    UNIQUE (seat_id)
);

CREATE TABLE bookings (
    booking_id UUID PRIMARY KEY,
    show_id    BIGINT NOT NULL
        REFERENCES shows(show_id) ON DELETE CASCADE,
    hold_id    UUID NOT NULL UNIQUE,
    booked_at  TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE booking_seats (
    booking_id UUID NOT NULL
        REFERENCES bookings(booking_id) ON DELETE CASCADE,
    seat_id    BIGINT NOT NULL
        REFERENCES seats(seat_id),
    PRIMARY KEY (booking_id, seat_id),
    UNIQUE (seat_id)
);


CREATE INDEX IF NOT EXISTS idx_seat_holds_active
ON seat_holds (show_id, expires_at);

CREATE INDEX IF NOT EXISTS idx_bookings_show
ON bookings (show_id);

