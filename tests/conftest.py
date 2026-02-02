import psycopg2
import pytest
from psycopg2.extras import RealDictCursor
from pytest_bdd import given


# -----------------------------------------------------
# Database connection (shared for all tests)
# -----------------------------------------------------

@pytest.fixture(scope="session")
def db_conn():
    """
    Creates a single PostgreSQL connection for the entire
    pytest session.

    Scope: session
    - Created once
    - Reused by all tests
    """
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="postgres",
        user="postgres",
        password="postgres",
        cursor_factory=RealDictCursor,
    )

    # We manage transactions manually in tests
    conn.autocommit = False

    yield conn

    conn.close()


# -----------------------------------------------------
# Clean database before each scenario
# -----------------------------------------------------

@pytest.fixture(autouse=True)
def clean_db(db_conn):
    """
    Ensures every BDD scenario starts with a clean database.

    autouse=True means:
    - This runs automatically
    - No test needs to explicitly request it
    """
    with db_conn.cursor() as cur:
        cur.execute("""
            TRUNCATE TABLE
                seat_holds,
                booking_seats,
                bookings,
                seats,
                shows
            RESTART IDENTITY
            CASCADE;
        """)
        db_conn.commit()

    yield


# -----------------------------------------------------
# Scenario context (shared state between steps)
# -----------------------------------------------------

@pytest.fixture
def context():
    """
    Simple dictionary used to share data between steps
    inside the same scenario.

    Example:
    context["show_id"]
    context["hold_id"]
    context["booking_id"]
    """
    return {}


# -----------------------------------------------------
# Shared GIVEN steps
# -----------------------------------------------------

@given("a show with 10 seats exists", target_fixture="show_id")
def show_with_10_seats(db_conn):
    """
    Inserts:
    - 1 show
    - exactly 10 seats

    Returns:
    - show_id (used by other steps)
    """
    with db_conn.cursor() as cur:
        # Create show
        cur.execute(
            """
            INSERT INTO shows (total_seats)
            VALUES (10)
            RETURNING show_id;
            """
        )
        show_id = cur.fetchone()["show_id"]

        # Create seats
        for seat_number in range(1, 11):
            cur.execute(
                """
                INSERT INTO seats (show_id, seat_number)
                VALUES (%s, %s);
                """,
                (show_id, seat_number),
            )

        db_conn.commit()

    return show_id
