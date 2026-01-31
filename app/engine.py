import uuid
from datetime import datetime, timedelta
from typing import Dict

import psycopg2
from psycopg2.extras import RealDictCursor


class SeatBookingEngine:
    """
    Core booking engine.
    ALL seat truth lives here.
    FastAPI must only call these methods.
    """

    def __init__(self, conn):
        self.conn = conn

    # ---------------------------
    # Availability (READ ONLY)
    # ---------------------------
    def get_availability(self, show_id: int):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    COUNT(*) FILTER (
                        WHERE NOT EXISTS (
                            SELECT 1
                            FROM booking_seats bs
                            WHERE bs.seat_id = s.seat_id
                        )
                        AND NOT EXISTS (
                            SELECT 1
                            FROM seat_holds sh
                            WHERE sh.seat_id = s.seat_id
                              AND sh.expires_at > now()
                        )
                    ) AS available,

                    COUNT(*) FILTER (
                        WHERE EXISTS (
                            SELECT 1
                            FROM seat_holds sh
                            WHERE sh.seat_id = s.seat_id
                              AND sh.expires_at > now()
                        )
                    ) AS held,

                    COUNT(*) FILTER (
                        WHERE EXISTS (
                            SELECT 1
                            FROM booking_seats bs
                            WHERE bs.seat_id = s.seat_id
                        )
                    ) AS booked
                FROM seats s
                WHERE s.show_id = %s;
                """,
                (show_id,),
            )

            available, held, booked = cur.fetchone()

        return {
            "available": available,
            "held": held,
            "booked": booked,
        }


    def hold_seats(
        self,
        show_id: int,
        seat_count: int,
        hold_duration_seconds: int,
    ) -> str:
        """
        Attempts to hold N available seats.
        Returns hold_id on success.
        Raises Exception on failure.
        """
        hold_id = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(seconds=hold_duration_seconds)

        try:
            with self.conn:
                with self.conn.cursor() as cur:
                    # Insert holds atomically
                    cur.execute(
                        """
                        INSERT INTO seat_holds (hold_id, show_id, seat_id, expires_at)
                        SELECT
                            %s,
                            %s,
                            s.seat_id,
                            %s
                        FROM seats s
                        LEFT JOIN booking_seats bs
                              ON bs.seat_id = s.seat_id
                        LEFT JOIN seat_holds sh
                              ON sh.seat_id = s.seat_id
                              AND sh.expires_at > now()
                        WHERE s.show_id = %s
                          AND bs.seat_id IS NULL
                          AND sh.seat_id IS NULL
                        ORDER BY s.seat_number
                        LIMIT %s
                        RETURNING seat_id;
                        """,
                        (
                            hold_id,
                            show_id,
                            expires_at,
                            show_id,
                            seat_count,
                        ),
                    )

                    rows = cur.fetchall()
                    if len(rows) < seat_count:
                        raise Exception("Not enough available seats")

            return hold_id

        except Exception:
            self.conn.rollback()
            raise

        
    def confirm_booking(self, hold_id: str) -> str:
      """
      Converts a valid (non-expired) hold into a booking.
      Operation is idempotent.
      Raises exception if hold is expired or invalid.
      """

      try:
          with self.conn:
              with self.conn.cursor() as cur:

                  # ---------------------------
                  # Lock and validate active hold FIRST
                  # ---------------------------
                  cur.execute(
                      """
                      SELECT seat_id, show_id
                      FROM seat_holds
                      WHERE hold_id = %s
                        AND expires_at > now()
                      FOR UPDATE
                      """,
                      (hold_id,),
                  )
                  holds = cur.fetchall()

                  if not holds:
                      raise Exception("Hold not found or expired")

                  show_id = holds[0][1]

                  # ---------------------------
                  # Idempotency check (SAFE now)
                  # ---------------------------
                  cur.execute(
                      """
                      SELECT booking_id
                      FROM bookings
                      WHERE hold_id = %s
                      """,
                      (hold_id,),
                  )
                  row = cur.fetchone()
                  if row:
                      return row[0]

                  booking_id = str(uuid.uuid4())

                  # ---------------------------
                  # Create booking
                  # ---------------------------
                  cur.execute(
                      """
                      INSERT INTO bookings (
                          booking_id,
                          show_id,
                          hold_id
                      )
                      VALUES (%s, %s, %s)
                      """,
                      (booking_id, show_id, hold_id),
                  )

                  # ---------------------------
                  # Attach seats
                  # ---------------------------
                  for seat_id, _ in holds:
                      cur.execute(
                          """
                          INSERT INTO booking_seats (
                              booking_id,
                              seat_id
                          )
                          VALUES (%s, %s)
                          """,
                          (booking_id, seat_id),
                      )

                  # ---------------------------
                  # Remove holds
                  # ---------------------------
                  cur.execute(
                      """
                      DELETE FROM seat_holds
                      WHERE hold_id = %s
                      """,
                      (hold_id,),
                  )

              return booking_id

      except Exception:
          self.conn.rollback()
          raise

