import getpass
import os
import time

import psycopg2
import psycopg2.extras

# Stored TIMESTAMP values have no time zone and are interpreted as UTC.
NOW_UTC = "(now() AT TIME ZONE 'UTC')"


class BusinessRuleError(Exception):
    pass


class SimulatedFailure(Exception):
    pass


def _database_url():
    """Cloud: DATABASE_URL env var or Streamlit secret. Local: None (use PG* vars)."""
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    try:
        import streamlit as st

        return st.secrets.get("DATABASE_URL")
    except Exception:
        return None


def connection_mode():
    """'cloud' when DATABASE_URL is configured, otherwise 'local'. Display only."""
    return "cloud" if _database_url() else "local"


def connect():
    url = _database_url()
    if url:
        # Used exactly as given: cloud URLs from Neon already end with
        # "?sslmode=require", which Neon requires. Do not force SSL here, so
        # the same code also works with a plain local DATABASE_URL.
        return psycopg2.connect(url)
    return psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "baggage_demo"),
        user=os.getenv("PGUSER", getpass.getuser()),
        password=os.getenv("PGPASSWORD", ""),
    )


def query(sql, params=None):
    conn = connect()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()


# ---------- Passenger ----------

def passenger_login(tag_code, email):
    rows = query(
        """
        SELECT p.passenger_id, p.name
        FROM Baggage b
        JOIN Passenger p ON p.passenger_id = b.passenger_id
        WHERE b.tag_code = %s AND LOWER(p.email) = LOWER(%s)
        """,
        (tag_code.strip(), email.strip()),
    )
    return rows[0] if rows else None


def passenger_bags(passenger_id):
    return query(
        """
        SELECT tag_code, weight
        FROM Baggage
        WHERE passenger_id = %s
        ORDER BY tag_code
        """,
        (passenger_id,),
    )


def latest_location(tag_code):
    rows = query(
        """
        SELECT tp.airport_code, a.name AS airport_name, tp.point_name,
               se.event_type, se.scanned_at, f.flight_number
        FROM Baggage b
        JOIN ScanEvent se ON se.baggage_id = b.baggage_id
        JOIN TrackingPoint tp ON tp.point_id = se.point_id
        JOIN Airport a ON a.airport_code = tp.airport_code
        LEFT JOIN Flight f ON f.flight_id = se.flight_id
        WHERE b.tag_code = %s
          AND NOT EXISTS (
              SELECT 1
              FROM ScanEvent newer
              WHERE newer.baggage_id = se.baggage_id
                AND (newer.scanned_at > se.scanned_at
                     OR (newer.scanned_at = se.scanned_at AND newer.scan_id > se.scan_id))
          )
        """,
        (tag_code,),
    )
    return rows[0] if rows else None


def itinerary(tag_code):
    return query(
        """
        SELECT bf.segment_order, f.flight_id, f.flight_number,
               f.departure_airport, f.arrival_airport,
               f.scheduled_departure, f.scheduled_arrival, bf.transport_status
        FROM BaggageFlight bf
        JOIN Baggage b ON b.baggage_id = bf.baggage_id
        JOIN Flight f ON f.flight_id = bf.flight_id
        WHERE b.tag_code = %s
        ORDER BY bf.segment_order
        """,
        (tag_code,),
    )


def scan_history(tag_code):
    return query(
        """
        SELECT se.scanned_at, tp.airport_code, tp.point_name,
               se.event_type, f.flight_number
        FROM ScanEvent se
        JOIN Baggage b ON b.baggage_id = se.baggage_id
        JOIN TrackingPoint tp ON tp.point_id = se.point_id
        LEFT JOIN Flight f ON f.flight_id = se.flight_id
        WHERE b.tag_code = %s
        ORDER BY se.scanned_at, se.scan_id
        """,
        (tag_code,),
    )


def open_report(tag_code):
    rows = query(
        """
        SELECT mr.report_id, mr.reported_at, mr.description
        FROM MissingReport mr
        JOIN Baggage b ON b.baggage_id = mr.baggage_id
        WHERE b.tag_code = %s AND mr.status = 'OPEN'
        """,
        (tag_code,),
    )
    return rows[0] if rows else None


# ---------- Staff ----------

def airports():
    return query("SELECT airport_code, name FROM Airport ORDER BY airport_code")


def flights():
    return query(
        """
        SELECT flight_id, flight_number, departure_airport, arrival_airport,
               scheduled_departure
        FROM Flight
        ORDER BY scheduled_departure, flight_number
        """
    )


def record_scan(tag_code, airport_code, point_type, event_type, flight_id):
    """Single-statement ground scan. LOADING and ARRIVAL go through advance_segment."""
    conn = connect()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO ScanEvent (baggage_id, point_id, flight_id, event_type, scanned_at)
                SELECT b.baggage_id, tp.point_id, %s, %s, {NOW_UTC}
                FROM Baggage b, TrackingPoint tp
                WHERE b.tag_code = %s
                  AND tp.airport_code = %s
                  AND tp.point_type = %s
                ORDER BY tp.point_id
                LIMIT 1
                RETURNING scan_id
                """,
                (flight_id, event_type, tag_code, airport_code, point_type),
            )
            row = cur.fetchone()
            if row is None:
                raise BusinessRuleError(
                    f"Bag {tag_code} not found, or {airport_code} has no {point_type} tracking point."
                )
            return row[0]
    finally:
        conn.close()


# Each action moves one BaggageFlight segment forward and records the matching scan.
SEGMENT_ACTIONS = {
    "LOAD": {
        "from_status": "ASSIGNED",
        "to_status": "LOADED",
        "event_type": "LOADING",
        "point_type": "LOADING",
        "airport_column": "departure_airport",
    },
    "ARRIVE": {
        "from_status": "LOADED",
        "to_status": "ARRIVED",
        "event_type": "ARRIVAL",
        "point_type": "ARRIVAL",
        "airport_column": "arrival_airport",
    },
}


def advance_segment(tag_code, flight_id, action, simulate_failure=False, hold_seconds=0):
    """
    Multi-step transaction:
      1. lock the BaggageFlight row (SELECT ... FOR UPDATE) and check its status;
      2. for loading, check the previous segment has ARRIVED;
      3. insert the LOADING / ARRIVAL ScanEvent;
      4. update BaggageFlight.transport_status.
    Any error rolls back every step, so a scan never exists without its status change.
    """
    rule = SEGMENT_ACTIONS[action]
    conn = connect()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT bf.baggage_id, bf.segment_order, bf.transport_status,
                       f.flight_number, f.{rule['airport_column']} AS airport_code
                FROM BaggageFlight bf
                JOIN Baggage b ON b.baggage_id = bf.baggage_id
                JOIN Flight f ON f.flight_id = bf.flight_id
                WHERE b.tag_code = %s AND bf.flight_id = %s
                FOR UPDATE OF bf
                """,
                (tag_code, flight_id),
            )
            seg = cur.fetchone()
            if seg is None:
                raise BusinessRuleError(f"This flight is not part of bag {tag_code}'s itinerary.")
            baggage_id, segment_order, status, flight_number, airport_code = seg

            if status != rule["from_status"]:
                raise BusinessRuleError(
                    f"Segment {flight_number} is {status}; it must be {rule['from_status']}."
                )

            if action == "LOAD" and segment_order > 1:
                cur.execute(
                    """
                    SELECT transport_status FROM BaggageFlight
                    WHERE baggage_id = %s AND segment_order = %s
                    """,
                    (baggage_id, segment_order - 1),
                )
                prev = cur.fetchone()
                if prev is None or prev[0] != "ARRIVED":
                    raise BusinessRuleError(
                        "The previous segment has not ARRIVED, so this segment cannot be loaded."
                    )

            cur.execute(
                f"""
                INSERT INTO ScanEvent (baggage_id, point_id, flight_id, event_type, scanned_at)
                SELECT %s, point_id, %s, %s, {NOW_UTC}
                FROM TrackingPoint
                WHERE airport_code = %s AND point_type = %s
                ORDER BY point_id
                LIMIT 1
                RETURNING scan_id
                """,
                (baggage_id, flight_id, rule["event_type"], airport_code, rule["point_type"]),
            )
            if cur.fetchone() is None:
                raise BusinessRuleError(f"{airport_code} has no {rule['point_type']} tracking point.")

            if hold_seconds:
                time.sleep(hold_seconds)
            if simulate_failure:
                raise SimulatedFailure(
                    "Simulated failure after inserting the scan, before updating the segment status."
                )

            cur.execute(
                """
                UPDATE BaggageFlight SET transport_status = %s
                WHERE baggage_id = %s AND flight_id = %s
                """,
                (rule["to_status"], baggage_id, flight_id),
            )
            return f"Bag {tag_code}: segment {flight_number} is now {rule['to_status']}."
    finally:
        conn.close()


def scan_count(tag_code):
    return query(
        """
        SELECT COUNT(*) AS n FROM ScanEvent se
        JOIN Baggage b ON b.baggage_id = se.baggage_id
        WHERE b.tag_code = %s
        """,
        (tag_code,),
    )[0]["n"]


# ---------- Manager dashboard ----------

def summary_counts():
    return query(
        """
        SELECT (SELECT COUNT(*) FROM Baggage) AS bags,
               (SELECT COUNT(*) FROM MissingReport WHERE status = 'OPEN') AS open_reports,
               (SELECT COUNT(*) FROM BaggageFlight WHERE transport_status = 'LOADED') AS in_flight
        """
    )[0]


def transfer_exceptions():
    return query(
        f"""
        SELECT b.tag_code, p.name AS passenger, bf.segment_order, f.flight_number,
               f.departure_airport, f.arrival_airport, f.scheduled_departure,
               bf.transport_status
        FROM BaggageFlight bf
        JOIN Baggage b ON b.baggage_id = bf.baggage_id
        JOIN Passenger p ON p.passenger_id = b.passenger_id
        JOIN Flight f ON f.flight_id = bf.flight_id
        JOIN BaggageFlight prev ON prev.baggage_id = bf.baggage_id
            AND prev.segment_order = bf.segment_order - 1
        JOIN Flight prev_f ON prev_f.flight_id = prev.flight_id
        WHERE bf.transport_status = 'ASSIGNED'
          AND prev.transport_status = 'ARRIVED'
          AND prev_f.arrival_airport = f.departure_airport
          AND f.scheduled_departure < {NOW_UTC}
        ORDER BY b.tag_code, bf.segment_order
        """
    )


def open_reports_by_airport():
    return query(
        """
        SELECT tp.airport_code AS last_recorded_airport, COUNT(*) AS open_reports
        FROM MissingReport mr
        JOIN ScanEvent se ON se.baggage_id = mr.baggage_id
        JOIN TrackingPoint tp ON tp.point_id = se.point_id
        WHERE mr.status = 'OPEN'
          AND NOT EXISTS (
              SELECT 1
              FROM ScanEvent newer
              WHERE newer.baggage_id = se.baggage_id
                AND (newer.scanned_at > se.scanned_at
                     OR (newer.scanned_at = se.scanned_at AND newer.scan_id > se.scan_id))
          )
        GROUP BY tp.airport_code
        ORDER BY tp.airport_code
        """
    )


def flight_load_progress():
    return query(
        """
        SELECT f.flight_number, f.departure_airport, f.arrival_airport, f.scheduled_departure,
               COUNT(bf.baggage_id) AS bags,
               SUM(CASE WHEN bf.transport_status = 'ASSIGNED' THEN 1 ELSE 0 END) AS assigned,
               SUM(CASE WHEN bf.transport_status = 'LOADED' THEN 1 ELSE 0 END) AS loaded,
               SUM(CASE WHEN bf.transport_status = 'ARRIVED' THEN 1 ELSE 0 END) AS arrived
        FROM Flight f
        LEFT JOIN BaggageFlight bf ON bf.flight_id = f.flight_id
        GROUP BY f.flight_id, f.flight_number, f.departure_airport, f.arrival_airport,
                 f.scheduled_departure
        ORDER BY f.scheduled_departure
        """
    )
