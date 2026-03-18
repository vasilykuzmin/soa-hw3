CREATE TYPE "FlightStatus" AS ENUM (
    'SCHEDULED',
    'DEPARTED',
    'CANCELLED',
    'COMPLETED'
);

CREATE TYPE "SeatReservationStatus" AS ENUM (
    'ACTIVE',
    'RELEASED',
    'EXPIRED'
);

CREATE TABLE "Flight" (
    "id" SERIAL PRIMARY KEY,
    "flight_number" varchar(7),
    "flight_date" date,
    "company" text,
    "origin" varchar(3),
    "destination" varchar(3),
    "departure_datetime" timestamp,
    "arrival_datetime" timestamp,
    "seat_capacity" integer,
    "seat_available" integer,
    "price" integer,
    "status" "FlightStatus",
    CHECK (seat_available >= 0),
    CHECK (seat_capacity > 0),
    CHECK (price > 0)
);

CREATE TABLE "SeatReservation" (
    "booking_id" integer PRIMARY KEY,
    "flight_id" integer,
    "seat_count" integer,
    "status" "SeatReservationStatus",
    CHECK (seat_count > 0)
);

CREATE UNIQUE INDEX ON "Flight" ("flight_number", "flight_date");
