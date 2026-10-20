-- COMP9120 sample data for the ORIGINAL Assignment1.sql schema.
-- Real airport identifiers; fictional passengers, TXZ flight schedules and baggage.
-- All TIMESTAMP values represent UTC, not airport local time.
-- Reference snapshot: 2026-10-17 12:00:00 UTC. No IDs are hard-coded.
-- Run 01_schema.sql first in a NEW, EMPTY sample database.
-- This script refuses to insert when any of the eight tables already has rows.

BEGIN;
SET LOCAL TIME ZONE 'UTC';

DO $seed_guard$
BEGIN
    IF EXISTS (
    SELECT 1 FROM Passenger
    UNION ALL
    SELECT 1 FROM Baggage
    UNION ALL
    SELECT 1 FROM Airport
    UNION ALL
    SELECT 1 FROM Flight
    UNION ALL
    SELECT 1 FROM BaggageFlight
    UNION ALL
    SELECT 1 FROM TrackingPoint
    UNION ALL
    SELECT 1 FROM ScanEvent
    UNION ALL
    SELECT 1 FROM MissingReport
    ) THEN
        RAISE EXCEPTION 'Sample data requires all eight tables to be empty. Use a separate sample database; existing rows will not be deleted.';
    END IF;
END;
$seed_guard$;

-- 1. Passengers: fictional names and Gmail-format addresses; mailbox ownership is not verified.
INSERT INTO Passenger (name, email) VALUES
    ('Amy Chen', 'txz9120.amy.chen.01@gmail.com'),
    ('Brian Lin', 'txz9120.brian.lin.02@gmail.com'),
    ('Chloe Wang', 'txz9120.chloe.wang.03@gmail.com'),
    ('Daniel Lee', 'txz9120.daniel.lee.04@gmail.com'),
    ('Eva Liu', 'txz9120.eva.liu.05@gmail.com'),
    ('Felix Wong', 'txz9120.felix.wong.06@gmail.com'),
    ('Haruto Sato', 'txz9120.haruto.sato.07@gmail.com'),
    ('Sofia Garcia', 'txz9120.sofia.garcia.08@gmail.com'),
    ('Lucas Silva', 'txz9120.lucas.silva.09@gmail.com'),
    ('Camille Laurent', 'txz9120.camille.laurent.10@gmail.com'),
    ('Lukas Weber', 'txz9120.lukas.weber.11@gmail.com'),
    ('Aarav Patel', 'txz9120.aarav.patel.12@gmail.com'),
    ('Minseo Kim', 'txz9120.minseo.kim.13@gmail.com'),
    ('Valentina Rojas', 'txz9120.valentina.rojas.14@gmail.com'),
    ('Liam Wilson', 'txz9120.liam.wilson.15@gmail.com'),
    ('Olivia Thompson', 'txz9120.olivia.thompson.16@gmail.com'),
    ('Jone Ravuvu', 'txz9120.jone.ravuvu.17@gmail.com'),
    ('Siti Rahman', 'txz9120.siti.rahman.18@gmail.com'),
    ('Amina Hassan', 'txz9120.amina.hassan.19@gmail.com'),
    ('Mateo Hernandez', 'txz9120.mateo.hernandez.20@gmail.com');

-- 2. Baggage: look up the passenger ID by the unique email in this fixture.
INSERT INTO Baggage (passenger_id, tag_code, weight) VALUES
    ((SELECT passenger_id FROM Passenger WHERE email = 'txz9120.amy.chen.01@gmail.com'), '100001', 23.40),
    ((SELECT passenger_id FROM Passenger WHERE email = 'txz9120.amy.chen.01@gmail.com'), '100002', 15.20),
    ((SELECT passenger_id FROM Passenger WHERE email = 'txz9120.brian.lin.02@gmail.com'), '100003', 19.00),
    ((SELECT passenger_id FROM Passenger WHERE email = 'txz9120.chloe.wang.03@gmail.com'), '100004', 21.70),
    ((SELECT passenger_id FROM Passenger WHERE email = 'txz9120.daniel.lee.04@gmail.com'), '100005', 17.30),
    ((SELECT passenger_id FROM Passenger WHERE email = 'txz9120.eva.liu.05@gmail.com'), '100006', 12.80),
    ((SELECT passenger_id FROM Passenger WHERE email = 'txz9120.felix.wong.06@gmail.com'), '100007', 24.10),
    ((SELECT passenger_id FROM Passenger WHERE email = 'txz9120.felix.wong.06@gmail.com'), '100008', 18.60);

-- 3. Airports: LA/LAX are the same selected airport; country/city choices are in README.txt.
INSERT INTO Airport (airport_code, name) VALUES
    ('YYZ', 'Toronto Pearson International Airport'),
    ('TPE', 'Taiwan Taoyuan International Airport'),
    ('BOG', 'El Dorado International Airport'),
    ('SYD', 'Sydney Airport'),
    ('NRT', 'Narita International Airport'),
    ('AKL', 'Auckland Airport'),
    ('LHR', 'Heathrow Airport'),
    ('CDG', 'Paris Charles de Gaulle Airport'),
    ('FRA', 'Frankfurt Airport'),
    ('AMS', 'Amsterdam Airport Schiphol'),
    ('LAX', 'Los Angeles International Airport'),
    ('SEA', 'Seattle-Tacoma International Airport'),
    ('JFK', 'John F. Kennedy International Airport'),
    ('IAD', 'Washington Dulles International Airport'),
    ('ORD', 'Chicago O''Hare International Airport'),
    ('HNL', 'Daniel K. Inouye International Airport'),
    ('NAN', 'Nadi International Airport'),
    ('MCO', 'Orlando International Airport'),
    ('PEK', 'Beijing Capital International Airport'),
    ('HKG', 'Hong Kong International Airport');

-- 4. Flights: fictional scheduled flight instances, including an unassigned PEK-HKG flight.
INSERT INTO Flight (flight_number, departure_airport, arrival_airport, scheduled_departure, scheduled_arrival) VALUES
    ('TXZ101', 'SYD', 'TPE', '2026-10-14 00:00:00', '2026-10-14 09:00:00'),
    ('TXZ102', 'TPE', 'NRT', '2026-10-14 11:00:00', '2026-10-14 14:30:00'),
    ('TXZ103', 'NRT', 'SEA', '2026-10-14 16:30:00', '2026-10-15 01:30:00'),
    ('TXZ201', 'YYZ', 'IAD', '2026-10-15 16:00:00', '2026-10-15 17:30:00'),
    ('TXZ202', 'IAD', 'LHR', '2026-10-15 19:30:00', '2026-10-16 03:00:00'),
    ('TXZ203', 'LHR', 'CDG', '2026-10-16 05:00:00', '2026-10-16 06:15:00'),
    ('TXZ301', 'BOG', 'LAX', '2026-10-15 12:00:00', '2026-10-15 19:30:00'),
    ('TXZ302', 'LAX', 'HNL', '2026-10-15 22:00:00', '2026-10-16 03:30:00'),
    ('TXZ401', 'AKL', 'NAN', '2026-10-15 00:00:00', '2026-10-15 03:00:00'),
    ('TXZ402', 'NAN', 'SYD', '2026-10-15 05:00:00', '2026-10-15 09:30:00'),
    ('TXZ501', 'FRA', 'AMS', '2026-10-17 15:00:00', '2026-10-17 16:15:00'),
    ('TXZ502', 'AMS', 'MCO', '2026-10-17 18:00:00', '2026-10-18 04:00:00'),
    ('TXZ601', 'LAX', 'SEA', '2026-10-15 12:00:00', '2026-10-15 14:45:00'),
    ('TXZ602', 'SEA', 'ORD', '2026-10-15 17:00:00', '2026-10-15 21:00:00'),
    ('TXZ603', 'ORD', 'JFK', '2026-10-15 23:00:00', '2026-10-16 01:30:00'),
    ('TXZ701', 'PEK', 'HKG', '2026-10-17 18:00:00', '2026-10-17 21:30:00');

-- 5. Planned baggage segments; IDs are looked up by tag and flight number.
INSERT INTO BaggageFlight (baggage_id, flight_id, segment_order, transport_status) VALUES
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100001'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ101'), 1, 'ARRIVED'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100001'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ102'), 2, 'ARRIVED'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100001'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ103'), 3, 'ARRIVED'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100002'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ101'), 1, 'ARRIVED'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100002'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ102'), 2, 'ARRIVED'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100002'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ103'), 3, 'ARRIVED'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100003'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ201'), 1, 'ARRIVED'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100003'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ202'), 2, 'ARRIVED'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100003'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ203'), 3, 'ASSIGNED'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100004'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ301'), 1, 'ARRIVED'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100004'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ302'), 2, 'ARRIVED'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100005'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ401'), 1, 'ARRIVED'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100005'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ402'), 2, 'ARRIVED'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100006'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ501'), 1, 'ASSIGNED'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100006'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ502'), 2, 'ASSIGNED'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100007'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ601'), 1, 'ARRIVED'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100007'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ602'), 2, 'ARRIVED'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100007'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ603'), 3, 'ARRIVED'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100008'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ601'), 1, 'ARRIVED'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100008'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ602'), 2, 'ASSIGNED'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100008'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ603'), 3, 'ASSIGNED');

-- 6. Six fictional tracking points per airport.
INSERT INTO TrackingPoint (airport_code, point_name, point_type) VALUES
    ('YYZ', 'YYZ Check-in Counter', 'CHECK_IN'),
    ('YYZ', 'YYZ Sorting Belt', 'SORTING'),
    ('YYZ', 'YYZ Loading Gate', 'LOADING'),
    ('YYZ', 'YYZ Transfer Hub', 'TRANSFER'),
    ('YYZ', 'YYZ Arrival Holding Area', 'ARRIVAL'),
    ('YYZ', 'YYZ Baggage Claim Carousel', 'BAGGAGE_CLAIM'),
    ('TPE', 'TPE Check-in Counter', 'CHECK_IN'),
    ('TPE', 'TPE Sorting Belt', 'SORTING'),
    ('TPE', 'TPE Loading Gate', 'LOADING'),
    ('TPE', 'TPE Transfer Hub', 'TRANSFER'),
    ('TPE', 'TPE Arrival Holding Area', 'ARRIVAL'),
    ('TPE', 'TPE Baggage Claim Carousel', 'BAGGAGE_CLAIM'),
    ('BOG', 'BOG Check-in Counter', 'CHECK_IN'),
    ('BOG', 'BOG Sorting Belt', 'SORTING'),
    ('BOG', 'BOG Loading Gate', 'LOADING'),
    ('BOG', 'BOG Transfer Hub', 'TRANSFER'),
    ('BOG', 'BOG Arrival Holding Area', 'ARRIVAL'),
    ('BOG', 'BOG Baggage Claim Carousel', 'BAGGAGE_CLAIM'),
    ('SYD', 'SYD Check-in Counter', 'CHECK_IN'),
    ('SYD', 'SYD Sorting Belt', 'SORTING'),
    ('SYD', 'SYD Loading Gate', 'LOADING'),
    ('SYD', 'SYD Transfer Hub', 'TRANSFER'),
    ('SYD', 'SYD Arrival Holding Area', 'ARRIVAL'),
    ('SYD', 'SYD Baggage Claim Carousel', 'BAGGAGE_CLAIM'),
    ('NRT', 'NRT Check-in Counter', 'CHECK_IN'),
    ('NRT', 'NRT Sorting Belt', 'SORTING'),
    ('NRT', 'NRT Loading Gate', 'LOADING'),
    ('NRT', 'NRT Transfer Hub', 'TRANSFER'),
    ('NRT', 'NRT Arrival Holding Area', 'ARRIVAL'),
    ('NRT', 'NRT Baggage Claim Carousel', 'BAGGAGE_CLAIM'),
    ('AKL', 'AKL Check-in Counter', 'CHECK_IN'),
    ('AKL', 'AKL Sorting Belt', 'SORTING'),
    ('AKL', 'AKL Loading Gate', 'LOADING'),
    ('AKL', 'AKL Transfer Hub', 'TRANSFER'),
    ('AKL', 'AKL Arrival Holding Area', 'ARRIVAL'),
    ('AKL', 'AKL Baggage Claim Carousel', 'BAGGAGE_CLAIM'),
    ('LHR', 'LHR Check-in Counter', 'CHECK_IN'),
    ('LHR', 'LHR Sorting Belt', 'SORTING'),
    ('LHR', 'LHR Loading Gate', 'LOADING'),
    ('LHR', 'LHR Transfer Hub', 'TRANSFER'),
    ('LHR', 'LHR Arrival Holding Area', 'ARRIVAL'),
    ('LHR', 'LHR Baggage Claim Carousel', 'BAGGAGE_CLAIM'),
    ('CDG', 'CDG Check-in Counter', 'CHECK_IN'),
    ('CDG', 'CDG Sorting Belt', 'SORTING'),
    ('CDG', 'CDG Loading Gate', 'LOADING'),
    ('CDG', 'CDG Transfer Hub', 'TRANSFER'),
    ('CDG', 'CDG Arrival Holding Area', 'ARRIVAL'),
    ('CDG', 'CDG Baggage Claim Carousel', 'BAGGAGE_CLAIM'),
    ('FRA', 'FRA Check-in Counter', 'CHECK_IN'),
    ('FRA', 'FRA Sorting Belt', 'SORTING'),
    ('FRA', 'FRA Loading Gate', 'LOADING'),
    ('FRA', 'FRA Transfer Hub', 'TRANSFER'),
    ('FRA', 'FRA Arrival Holding Area', 'ARRIVAL'),
    ('FRA', 'FRA Baggage Claim Carousel', 'BAGGAGE_CLAIM'),
    ('AMS', 'AMS Check-in Counter', 'CHECK_IN'),
    ('AMS', 'AMS Sorting Belt', 'SORTING'),
    ('AMS', 'AMS Loading Gate', 'LOADING'),
    ('AMS', 'AMS Transfer Hub', 'TRANSFER'),
    ('AMS', 'AMS Arrival Holding Area', 'ARRIVAL'),
    ('AMS', 'AMS Baggage Claim Carousel', 'BAGGAGE_CLAIM'),
    ('LAX', 'LAX Check-in Counter', 'CHECK_IN'),
    ('LAX', 'LAX Sorting Belt', 'SORTING'),
    ('LAX', 'LAX Loading Gate', 'LOADING'),
    ('LAX', 'LAX Transfer Hub', 'TRANSFER'),
    ('LAX', 'LAX Arrival Holding Area', 'ARRIVAL'),
    ('LAX', 'LAX Baggage Claim Carousel', 'BAGGAGE_CLAIM'),
    ('SEA', 'SEA Check-in Counter', 'CHECK_IN'),
    ('SEA', 'SEA Sorting Belt', 'SORTING'),
    ('SEA', 'SEA Loading Gate', 'LOADING'),
    ('SEA', 'SEA Transfer Hub', 'TRANSFER'),
    ('SEA', 'SEA Arrival Holding Area', 'ARRIVAL'),
    ('SEA', 'SEA Baggage Claim Carousel', 'BAGGAGE_CLAIM'),
    ('JFK', 'JFK Check-in Counter', 'CHECK_IN'),
    ('JFK', 'JFK Sorting Belt', 'SORTING'),
    ('JFK', 'JFK Loading Gate', 'LOADING'),
    ('JFK', 'JFK Transfer Hub', 'TRANSFER'),
    ('JFK', 'JFK Arrival Holding Area', 'ARRIVAL'),
    ('JFK', 'JFK Baggage Claim Carousel', 'BAGGAGE_CLAIM'),
    ('IAD', 'IAD Check-in Counter', 'CHECK_IN'),
    ('IAD', 'IAD Sorting Belt', 'SORTING'),
    ('IAD', 'IAD Loading Gate', 'LOADING'),
    ('IAD', 'IAD Transfer Hub', 'TRANSFER'),
    ('IAD', 'IAD Arrival Holding Area', 'ARRIVAL'),
    ('IAD', 'IAD Baggage Claim Carousel', 'BAGGAGE_CLAIM'),
    ('ORD', 'ORD Check-in Counter', 'CHECK_IN'),
    ('ORD', 'ORD Sorting Belt', 'SORTING'),
    ('ORD', 'ORD Loading Gate', 'LOADING'),
    ('ORD', 'ORD Transfer Hub', 'TRANSFER'),
    ('ORD', 'ORD Arrival Holding Area', 'ARRIVAL'),
    ('ORD', 'ORD Baggage Claim Carousel', 'BAGGAGE_CLAIM'),
    ('HNL', 'HNL Check-in Counter', 'CHECK_IN'),
    ('HNL', 'HNL Sorting Belt', 'SORTING'),
    ('HNL', 'HNL Loading Gate', 'LOADING'),
    ('HNL', 'HNL Transfer Hub', 'TRANSFER'),
    ('HNL', 'HNL Arrival Holding Area', 'ARRIVAL'),
    ('HNL', 'HNL Baggage Claim Carousel', 'BAGGAGE_CLAIM'),
    ('NAN', 'NAN Check-in Counter', 'CHECK_IN'),
    ('NAN', 'NAN Sorting Belt', 'SORTING'),
    ('NAN', 'NAN Loading Gate', 'LOADING'),
    ('NAN', 'NAN Transfer Hub', 'TRANSFER'),
    ('NAN', 'NAN Arrival Holding Area', 'ARRIVAL'),
    ('NAN', 'NAN Baggage Claim Carousel', 'BAGGAGE_CLAIM'),
    ('MCO', 'MCO Check-in Counter', 'CHECK_IN'),
    ('MCO', 'MCO Sorting Belt', 'SORTING'),
    ('MCO', 'MCO Loading Gate', 'LOADING'),
    ('MCO', 'MCO Transfer Hub', 'TRANSFER'),
    ('MCO', 'MCO Arrival Holding Area', 'ARRIVAL'),
    ('MCO', 'MCO Baggage Claim Carousel', 'BAGGAGE_CLAIM'),
    ('PEK', 'PEK Check-in Counter', 'CHECK_IN'),
    ('PEK', 'PEK Sorting Belt', 'SORTING'),
    ('PEK', 'PEK Loading Gate', 'LOADING'),
    ('PEK', 'PEK Transfer Hub', 'TRANSFER'),
    ('PEK', 'PEK Arrival Holding Area', 'ARRIVAL'),
    ('PEK', 'PEK Baggage Claim Carousel', 'BAGGAGE_CLAIM'),
    ('HKG', 'HKG Check-in Counter', 'CHECK_IN'),
    ('HKG', 'HKG Sorting Belt', 'SORTING'),
    ('HKG', 'HKG Loading Gate', 'LOADING'),
    ('HKG', 'HKG Transfer Hub', 'TRANSFER'),
    ('HKG', 'HKG Arrival Holding Area', 'ARRIVAL'),
    ('HKG', 'HKG Baggage Claim Carousel', 'BAGGAGE_CLAIM');

-- 7. Scan history. NULL flight IDs illustrate flight-independent sorting scans.
INSERT INTO ScanEvent (baggage_id, point_id, flight_id, event_type, scanned_at) VALUES
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100001'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'SYD' AND point_type = 'CHECK_IN'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ101'), 'CHECK_IN', '2026-10-13 22:00:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100001'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'SYD' AND point_type = 'SORTING'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ101'), 'SORTING', '2026-10-13 22:10:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100001'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'SYD' AND point_type = 'LOADING'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ101'), 'LOADING', '2026-10-13 23:10:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100001'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'TPE' AND point_type = 'ARRIVAL'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ101'), 'ARRIVAL', '2026-10-14 09:05:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100001'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'TPE' AND point_type = 'TRANSFER'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ101'), 'TRANSFER_IN', '2026-10-14 09:10:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100001'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'TPE' AND point_type = 'TRANSFER'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ102'), 'TRANSFER_OUT', '2026-10-14 10:20:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100001'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'TPE' AND point_type = 'LOADING'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ102'), 'LOADING', '2026-10-14 10:30:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100001'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'NRT' AND point_type = 'ARRIVAL'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ102'), 'ARRIVAL', '2026-10-14 14:35:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100001'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'NRT' AND point_type = 'TRANSFER'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ102'), 'TRANSFER_IN', '2026-10-14 14:40:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100001'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'NRT' AND point_type = 'TRANSFER'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ103'), 'TRANSFER_OUT', '2026-10-14 15:50:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100001'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'NRT' AND point_type = 'LOADING'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ103'), 'LOADING', '2026-10-14 16:00:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100001'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'SEA' AND point_type = 'ARRIVAL'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ103'), 'ARRIVAL', '2026-10-15 01:35:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100001'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'SEA' AND point_type = 'BAGGAGE_CLAIM'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ103'), 'COLLECTED', '2026-10-15 01:55:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100002'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'SYD' AND point_type = 'CHECK_IN'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ101'), 'CHECK_IN', '2026-10-13 22:02:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100002'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'SYD' AND point_type = 'SORTING'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ101'), 'SORTING', '2026-10-13 22:12:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100002'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'SYD' AND point_type = 'LOADING'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ101'), 'LOADING', '2026-10-13 23:12:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100002'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'TPE' AND point_type = 'ARRIVAL'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ101'), 'ARRIVAL', '2026-10-14 09:07:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100002'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'TPE' AND point_type = 'TRANSFER'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ101'), 'TRANSFER_IN', '2026-10-14 09:12:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100002'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'TPE' AND point_type = 'TRANSFER'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ102'), 'TRANSFER_OUT', '2026-10-14 10:22:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100002'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'TPE' AND point_type = 'LOADING'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ102'), 'LOADING', '2026-10-14 10:32:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100002'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'NRT' AND point_type = 'ARRIVAL'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ102'), 'ARRIVAL', '2026-10-14 14:37:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100002'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'NRT' AND point_type = 'TRANSFER'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ102'), 'TRANSFER_IN', '2026-10-14 14:42:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100002'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'NRT' AND point_type = 'TRANSFER'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ103'), 'TRANSFER_OUT', '2026-10-14 15:52:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100002'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'NRT' AND point_type = 'LOADING'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ103'), 'LOADING', '2026-10-14 16:02:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100002'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'SEA' AND point_type = 'ARRIVAL'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ103'), 'ARRIVAL', '2026-10-15 01:37:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100002'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'SEA' AND point_type = 'BAGGAGE_CLAIM'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ103'), 'COLLECTED', '2026-10-15 01:57:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100003'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'YYZ' AND point_type = 'CHECK_IN'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ201'), 'CHECK_IN', '2026-10-15 14:00:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100003'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'YYZ' AND point_type = 'SORTING'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ201'), 'SORTING', '2026-10-15 14:10:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100003'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'YYZ' AND point_type = 'LOADING'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ201'), 'LOADING', '2026-10-15 15:00:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100003'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'IAD' AND point_type = 'ARRIVAL'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ201'), 'ARRIVAL', '2026-10-15 17:35:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100003'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'IAD' AND point_type = 'TRANSFER'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ201'), 'TRANSFER_IN', '2026-10-15 17:45:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100003'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'IAD' AND point_type = 'TRANSFER'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ202'), 'TRANSFER_OUT', '2026-10-15 18:40:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100003'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'IAD' AND point_type = 'LOADING'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ202'), 'LOADING', '2026-10-15 18:50:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100003'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'LHR' AND point_type = 'ARRIVAL'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ202'), 'ARRIVAL', '2026-10-16 03:05:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100003'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'LHR' AND point_type = 'TRANSFER'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ202'), 'TRANSFER_IN', '2026-10-16 03:15:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100003'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'LHR' AND point_type = 'SORTING'), NULL, 'SORTING', '2026-10-16 03:25:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100004'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'BOG' AND point_type = 'CHECK_IN'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ301'), 'CHECK_IN', '2026-10-15 10:00:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100004'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'BOG' AND point_type = 'SORTING'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ301'), 'SORTING', '2026-10-15 10:10:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100004'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'BOG' AND point_type = 'LOADING'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ301'), 'LOADING', '2026-10-15 11:00:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100004'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'LAX' AND point_type = 'ARRIVAL'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ301'), 'ARRIVAL', '2026-10-15 19:35:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100004'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'LAX' AND point_type = 'TRANSFER'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ301'), 'TRANSFER_IN', '2026-10-15 19:45:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100004'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'LAX' AND point_type = 'TRANSFER'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ302'), 'TRANSFER_OUT', '2026-10-15 21:00:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100004'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'LAX' AND point_type = 'LOADING'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ302'), 'LOADING', '2026-10-15 21:10:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100004'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'HNL' AND point_type = 'ARRIVAL'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ302'), 'ARRIVAL', '2026-10-16 03:35:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100005'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'AKL' AND point_type = 'CHECK_IN'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ401'), 'CHECK_IN', '2026-10-14 22:00:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100005'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'AKL' AND point_type = 'SORTING'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ401'), 'SORTING', '2026-10-14 22:10:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100005'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'AKL' AND point_type = 'LOADING'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ401'), 'LOADING', '2026-10-14 23:10:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100005'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'NAN' AND point_type = 'ARRIVAL'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ401'), 'ARRIVAL', '2026-10-15 03:05:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100005'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'NAN' AND point_type = 'TRANSFER'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ401'), 'TRANSFER_IN', '2026-10-15 03:15:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100005'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'NAN' AND point_type = 'TRANSFER'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ402'), 'TRANSFER_OUT', '2026-10-15 04:10:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100005'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'NAN' AND point_type = 'LOADING'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ402'), 'LOADING', '2026-10-15 04:20:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100005'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'SYD' AND point_type = 'ARRIVAL'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ402'), 'ARRIVAL', '2026-10-15 09:35:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100005'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'SYD' AND point_type = 'SORTING'), NULL, 'SORTING', '2026-10-15 12:00:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100005'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'SYD' AND point_type = 'BAGGAGE_CLAIM'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ402'), 'COLLECTED', '2026-10-15 12:30:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100006'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'FRA' AND point_type = 'CHECK_IN'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ501'), 'CHECK_IN', '2026-10-17 11:00:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100006'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'FRA' AND point_type = 'SORTING'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ501'), 'SORTING', '2026-10-17 11:10:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100007'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'LAX' AND point_type = 'CHECK_IN'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ601'), 'CHECK_IN', '2026-10-15 10:00:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100007'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'LAX' AND point_type = 'SORTING'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ601'), 'SORTING', '2026-10-15 10:10:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100007'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'LAX' AND point_type = 'LOADING'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ601'), 'LOADING', '2026-10-15 11:10:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100007'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'SEA' AND point_type = 'ARRIVAL'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ601'), 'ARRIVAL', '2026-10-15 14:50:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100007'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'SEA' AND point_type = 'TRANSFER'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ601'), 'TRANSFER_IN', '2026-10-15 15:00:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100007'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'SEA' AND point_type = 'TRANSFER'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ602'), 'TRANSFER_OUT', '2026-10-15 16:00:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100007'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'SEA' AND point_type = 'LOADING'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ602'), 'LOADING', '2026-10-15 16:10:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100007'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'ORD' AND point_type = 'ARRIVAL'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ602'), 'ARRIVAL', '2026-10-15 21:05:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100007'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'ORD' AND point_type = 'TRANSFER'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ602'), 'TRANSFER_IN', '2026-10-15 21:15:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100007'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'ORD' AND point_type = 'TRANSFER'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ603'), 'TRANSFER_OUT', '2026-10-15 22:00:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100007'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'ORD' AND point_type = 'LOADING'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ603'), 'LOADING', '2026-10-15 22:10:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100007'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'JFK' AND point_type = 'ARRIVAL'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ603'), 'ARRIVAL', '2026-10-16 01:35:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100007'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'JFK' AND point_type = 'BAGGAGE_CLAIM'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ603'), 'COLLECTED', '2026-10-16 01:55:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100008'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'LAX' AND point_type = 'CHECK_IN'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ601'), 'CHECK_IN', '2026-10-15 10:02:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100008'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'LAX' AND point_type = 'SORTING'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ601'), 'SORTING', '2026-10-15 10:12:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100008'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'LAX' AND point_type = 'LOADING'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ601'), 'LOADING', '2026-10-15 11:12:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100008'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'SEA' AND point_type = 'ARRIVAL'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ601'), 'ARRIVAL', '2026-10-15 14:52:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100008'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'SEA' AND point_type = 'TRANSFER'), (SELECT flight_id FROM Flight WHERE flight_number = 'TXZ601'), 'TRANSFER_IN', '2026-10-15 15:02:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100008'), (SELECT point_id FROM TrackingPoint WHERE airport_code = 'SEA' AND point_type = 'SORTING'), NULL, 'SORTING', '2026-10-15 15:12:00');

-- 8. Missing reports: two OPEN cases and one RESOLVED case.
INSERT INTO MissingReport (baggage_id, reported_at, description, status, resolved_at) VALUES
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100004'), '2026-10-16 04:30:00', 'Passenger reached HNL but the bag was not delivered to baggage claim. Last recorded at the HNL arrival holding area.', 'OPEN', NULL),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100005'), '2026-10-15 10:30:00', 'Bag missing at SYD baggage claim. Located at the sorting belt and collected by the passenger at 12:30 UTC.', 'RESOLVED', '2026-10-15 12:35:00'),
    ((SELECT baggage_id FROM Baggage WHERE tag_code = '100008'), '2026-10-16 02:30:00', 'Passenger reached JFK with one bag. This second bag was last scanned at SEA and has no loading confirmation for TXZ602.', 'OPEN', NULL);

-- Fail the entire import if any reference lookup silently lost or duplicated a row.
DO $seed_counts$
BEGIN
    IF (SELECT COUNT(*) FROM Passenger) <> 20
       OR (SELECT COUNT(*) FROM Baggage) <> 8
       OR (SELECT COUNT(*) FROM Airport) <> 20
       OR (SELECT COUNT(*) FROM Flight) <> 16
       OR (SELECT COUNT(*) FROM BaggageFlight) <> 21
       OR (SELECT COUNT(*) FROM TrackingPoint) <> 120
       OR (SELECT COUNT(*) FROM ScanEvent) <> 75
       OR (SELECT COUNT(*) FROM MissingReport) <> 3 THEN
        RAISE EXCEPTION 'Unexpected row counts. The sample-data import has been cancelled.';
    END IF;
END;
$seed_counts$;

COMMIT;
