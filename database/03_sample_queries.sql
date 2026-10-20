-- Read-only sample queries for the sample data.
-- Every stored timestamp is UTC. Fixed snapshot: 2026-10-17 12:00:00 UTC.
-- These queries are examples, not a complete implementation of all assignment workflows.

-- Q1. Row counts in all eight tables.
SELECT 'Passenger' AS table_name, COUNT(*) AS row_count FROM Passenger
UNION ALL SELECT 'Baggage', COUNT(*) FROM Baggage
UNION ALL SELECT 'Airport', COUNT(*) FROM Airport
UNION ALL SELECT 'Flight', COUNT(*) FROM Flight
UNION ALL SELECT 'BaggageFlight', COUNT(*) FROM BaggageFlight
UNION ALL SELECT 'TrackingPoint', COUNT(*) FROM TrackingPoint
UNION ALL SELECT 'ScanEvent', COUNT(*) FROM ScanEvent
UNION ALL SELECT 'MissingReport', COUNT(*) FROM MissingReport;

-- Q2. Full tracking history for one bag. Change this tag to inspect another bag.
SELECT b.tag_code, p.name AS passenger_name, se.scanned_at AS scanned_at_utc,
       tp.airport_code, tp.point_name, se.event_type, f.flight_number
FROM ScanEvent se
JOIN Baggage b ON b.baggage_id = se.baggage_id
JOIN Passenger p ON p.passenger_id = b.passenger_id
JOIN TrackingPoint tp ON tp.point_id = se.point_id
LEFT JOIN Flight f ON f.flight_id = se.flight_id
WHERE b.tag_code = '100001'
ORDER BY se.scanned_at, se.scan_id;

-- Q3. Last RECORDED location, not a claim about the bag's real-time physical location.
-- A scan is latest when no later scan exists for the same bag.
SELECT b.tag_code, p.name AS passenger_name, b.weight,
       tp.airport_code AS last_recorded_airport, tp.point_name,
       rs.event_type AS latest_event, rs.scanned_at AS scanned_at_utc
FROM Baggage b
JOIN Passenger p ON p.passenger_id = b.passenger_id
LEFT JOIN ScanEvent rs ON rs.baggage_id = b.baggage_id
    AND NOT EXISTS (
        SELECT 1
        FROM ScanEvent newer
        WHERE newer.baggage_id = rs.baggage_id
          AND (newer.scanned_at > rs.scanned_at
               OR (newer.scanned_at = rs.scanned_at AND newer.scan_id > rs.scan_id))
    )
LEFT JOIN TrackingPoint tp ON tp.point_id = rs.point_id
ORDER BY b.tag_code;

-- Q4. Potential transfer exceptions: previous segment ARRIVED, next segment still
-- ASSIGNED after its scheduled departure. This flags missing loading confirmation
-- for staff review; it does not prove a real flight departed or a bag was lost.
-- Expected sample tags: 100003 and 100008.
SELECT b.tag_code, p.name AS passenger_name, bf.segment_order,
       f.flight_number, f.departure_airport, f.arrival_airport,
       f.scheduled_departure AS scheduled_departure_utc, bf.transport_status,
       CAST('2026-10-17 12:00:00' AS TIMESTAMP) AS as_of_utc
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
  AND f.scheduled_departure < CAST('2026-10-17 12:00:00' AS TIMESTAMP)
ORDER BY b.tag_code, bf.segment_order;

-- Q5. Missing reports, including the recovered-and-resolved case.
SELECT b.tag_code, p.name AS passenger_name, mr.status,
       mr.reported_at AS reported_at_utc, mr.resolved_at AS resolved_at_utc,
       mr.description
FROM MissingReport mr
JOIN Baggage b ON b.baggage_id = mr.baggage_id
JOIN Passenger p ON p.passenger_id = b.passenger_id
ORDER BY b.tag_code;

-- Q6. Number of open reports grouped by last recorded airport.
-- Expected: HNL = 1 and SEA = 1.
SELECT tp.airport_code AS last_recorded_airport, COUNT(*) AS open_report_count
FROM MissingReport mr
JOIN ScanEvent rs ON rs.baggage_id = mr.baggage_id
JOIN TrackingPoint tp ON tp.point_id = rs.point_id
WHERE mr.status = 'OPEN'
  AND NOT EXISTS (
      SELECT 1
      FROM ScanEvent newer
      WHERE newer.baggage_id = rs.baggage_id
        AND (newer.scanned_at > rs.scanned_at
             OR (newer.scanned_at = rs.scanned_at AND newer.scan_id > rs.scan_id))
  )
GROUP BY tp.airport_code
ORDER BY tp.airport_code;

-- Q7. All passengers, including people who have not checked in any baggage.
-- Expected: 20 passengers; the 14 newly added passengers have baggage_count = 0.
SELECT p.passenger_id, p.name, p.email, COUNT(b.baggage_id) AS baggage_count
FROM Passenger p
LEFT JOIN Baggage b ON b.passenger_id = p.passenger_id
GROUP BY p.passenger_id, p.name, p.email
ORDER BY p.passenger_id;
