CREATE TYPE "BookingStatus" AS ENUM (
  'CONFIRMED',
  'CANCELLED'
);

CREATE TABLE "Booking" (
  "id" SERIAL PRIMARY KEY,
  "flight_id" integer,
  "passenger_name" varchar(64),
  "passenger_email" varchar(64),
  "seat_count" integer,
  "price" integer,
  "status" "BookingStatus",
  CHECK (seat_count > 0),
  CHECK (price > 0)
);
