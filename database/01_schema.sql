CREATE TABLE Passenger (
    passenger_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255)
);

CREATE TABLE Baggage (
    baggage_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    passenger_id INTEGER NOT NULL,
    tag_code VARCHAR(30) UNIQUE NOT NULL,
    weight NUMERIC(5,2) NOT NULL CHECK (weight > 0),

    FOREIGN KEY (passenger_id)
        REFERENCES Passenger(passenger_id)
);

CREATE TABLE Airport (
    airport_code VARCHAR(3) PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE Flight (
    flight_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    flight_number VARCHAR(10) NOT NULL,
    departure_airport VARCHAR(3) NOT NULL,
    arrival_airport VARCHAR(3) NOT NULL,
    scheduled_departure TIMESTAMP NOT NULL,
    scheduled_arrival TIMESTAMP NOT NULL,

    FOREIGN KEY (departure_airport)
        REFERENCES Airport(airport_code),

    FOREIGN KEY (arrival_airport)
        REFERENCES Airport(airport_code),

    CHECK (departure_airport <> arrival_airport),
    CHECK (scheduled_arrival > scheduled_departure)
);

CREATE TABLE BaggageFlight (
    baggage_id INTEGER NOT NULL,
    flight_id INTEGER NOT NULL,
    segment_order INTEGER NOT NULL,
    transport_status VARCHAR(20) NOT NULL DEFAULT 'ASSIGNED',

    PRIMARY KEY (baggage_id, flight_id),

    FOREIGN KEY (baggage_id)
        REFERENCES Baggage(baggage_id),

    FOREIGN KEY (flight_id)
        REFERENCES Flight(flight_id),

    UNIQUE (baggage_id, segment_order),

    CHECK (segment_order > 0),

    CHECK (transport_status IN (
        'ASSIGNED',
        'LOADED',
        'ARRIVED'
    ))
);

CREATE TABLE IF NOT EXISTS TrackingPoint (
    point_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    airport_code VARCHAR(3) NOT NULL,
    point_name VARCHAR(100) NOT NULL,
    point_type VARCHAR(30) NOT NULL,

    FOREIGN KEY (airport_code)
        REFERENCES Airport(airport_code),

    CHECK (point_type IN (
        'CHECK_IN',
        'SORTING',
        'LOADING',
        'TRANSFER',
        'ARRIVAL',
        'BAGGAGE_CLAIM'
    ))
);

CREATE TABLE IF NOT EXISTS ScanEvent (
    scan_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    baggage_id INTEGER NOT NULL,
    point_id INTEGER NOT NULL,
    flight_id INTEGER,
    event_type VARCHAR(30) NOT NULL,
    scanned_at TIMESTAMP NOT NULL,

    FOREIGN KEY (baggage_id)
        REFERENCES Baggage(baggage_id),

    FOREIGN KEY (point_id)
        REFERENCES TrackingPoint(point_id),

    FOREIGN KEY (baggage_id, flight_id)
        REFERENCES BaggageFlight(baggage_id, flight_id),

    CHECK (event_type IN (
        'CHECK_IN',
        'SORTING',
        'LOADING',
        'TRANSFER_IN',
        'TRANSFER_OUT',
        'ARRIVAL',
        'COLLECTED'
    )),

    CHECK (
        event_type <> 'LOADING'
        OR flight_id IS NOT NULL
    )
);

CREATE TABLE MissingReport (
    report_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    baggage_id INTEGER NOT NULL,
    reported_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
    resolved_at TIMESTAMP,

    FOREIGN KEY (baggage_id)
        REFERENCES Baggage(baggage_id),

    CHECK (status IN ('OPEN', 'RESOLVED')),

    CHECK (
        (status = 'OPEN' AND resolved_at IS NULL)
        OR
        (status = 'RESOLVED' AND resolved_at IS NOT NULL)
    ),

    CHECK (
        resolved_at IS NULL
        OR resolved_at >= reported_at
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS one_open_report_per_baggage
ON MissingReport (baggage_id)
WHERE status = 'OPEN';