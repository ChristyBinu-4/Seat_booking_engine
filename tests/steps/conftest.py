import os
import psycopg2
import pytest
import requests
import uuid

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@db:5432/postgres"
)


@pytest.fixture(scope="session")
def db_conn():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    yield conn
    conn.close()


@pytest.fixture
def cursor(db_conn):
    cur = db_conn.cursor()
    yield cur
    db_conn.rollback()
    cur.close()


@pytest.fixture
def show_id(cursor):
    show_id = str(uuid.uuid4())

    cursor.execute(
        "INSERT INTO shows (show_id, total_seats) VALUES (%s, %s)",
        (show_id, 10),
    )

    for i in range(1, 11):
        cursor.execute(
            """
            INSERT INTO seats (seat_id, show_id, seat_number)
            VALUES (%s, %s, %s)
            """,
            (str(uuid.uuid4()), show_id, i),
        )

    return show_id


@pytest.fixture
def context():
    """
    Shared mutable context for steps
    """
    return {}
