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
    def get_availability(self, show_id: str):
      with self.conn.cursor() as cur:
          # total seats
          cur.execute(
              "SELECT COUNT(*) FROM seats WHERE show_id = %s",
              (show_id,),
          )
          total = cur.fetchone()[0]

          # booked seats (distinct seat_id)
          cur.execute(
              """
              SELECT COUNT(DISTINCT seat_id)
              FROM bookings
              WHERE show_id = %s
              """,
              (show_id,),
          )
          booked = cur.fetchone()[0]

          # held seats (distinct seat_id, only active holds)
          cur.execute(
              """
              SELECT COUNT(DISTINCT seat_id)
              FROM seat_holds
              WHERE show_id = %s
                AND expires_at > now()
              """,
              (show_id,),
          )
          held = cur.fetchone()[0]

      return {
          "available": total - booked - held,
          "held": held,
          "booked": booked,
      }

    def hold_seats(
      self,
      show_id: str,
      seat_count: int,
      hold_duration_seconds: int,) -> str:
      """
      Attempts to hold N available seats.
      Returns hold_id on success.
      Raises Exception on failure.
      """
      hold_id = str(uuid.uuid4())
      expires_at = datetime.now() + timedelta(
        seconds=hold_duration_seconds
      )

      try:
          with self.conn:
              with self.conn.cursor() as cur:
                  # Lock available seats (DETERMINISTIC ORDER IS CRITICAL)
                  cur.execute(
                      """
                      SELECT s.seat_id
                      FROM seats s
                      WHERE s.show_id = %s
                        AND NOT EXISTS (
                            SELECT 1 FROM bookings b
                            WHERE b.seat_id = s.seat_id
                        )
                        AND NOT EXISTS (
                            SELECT 1 FROM seat_holds h
                            WHERE h.seat_id = s.seat_id
                              AND h.expires_at > now()
                        )
                      ORDER BY s.seat_number
                      FOR UPDATE SKIP LOCKED
                      LIMIT %s
                      """,
                      (show_id, seat_count),
                  )

                  rows = cur.fetchall()
                  if len(rows) < seat_count:
                      raise Exception("Not enough available seats")

                  # Insert holds
                  for (seat_id,) in rows:
                      cur.execute(
                          """
                          INSERT INTO seat_holds (
                              hold_id, show_id, seat_id, expires_at
                          )
                          VALUES (%s, %s, %s, %s)
                          """,
                          (hold_id, show_id, seat_id, expires_at),
                      )

          return hold_id

      except Exception:
          self.conn.rollback()
          raise
        
    def confirm_booking(self, hold_id: str) -> str:
        """
        Converts a valid hold into a booking.
        Operation is idempotent.
        Returns booking_id.
        """

        try:
            with self.conn:
                with self.conn.cursor() as cur:

                    # ---------------------------
                    # Idempotency check
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

                    # ---------------------------
                    # Lock all seats for this hold
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

                    # All seats belong to the same show
                    show_id = holds[0][1]
                    booking_id = str(uuid.uuid4())

                    # ---------------------------
                    # Create booking (ONE row)
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
                    # Attach seats to booking
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
