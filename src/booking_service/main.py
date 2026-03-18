from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import os
import grpc
from google.protobuf.json_format import MessageToDict
import psycopg2
from psycopg2 import pool

import contract_pb2_grpc
import contract_pb2


app = FastAPI()

GRPC_SERVER_ADDR = os.getenv("GRPC_SERVER", "localhost:50051")

channel = None
client = None

postgres_connection_pool = None


class BookingRequst(BaseModel):
    user_id: int
    flight_id: int
    passenger_name: str
    passenger_email: str
    seat_count: int


@app.on_event("startup")
async def startup():
    global channel, client
    channel = grpc.aio.insecure_channel(GRPC_SERVER_ADDR)
    client = contract_pb2_grpc.FlightServiceStub(channel)

    global postgres_connection_pool

    postgres_connection_pool = pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=20,
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        database=os.getenv("POSTGRES_DB", "flight_service"),
        user=os.getenv("POSTGRES_USER", "user"),
        password=os.getenv("POSTGRES_PASSWORD", "mypass")
    )

@app.on_event("shutdown")
async def shutdown():
    await channel.close()


@app.get("/flights")
async def search_flights(origin: str, destination: str, date: str | None = None):
    try:
        request = contract_pb2.SearchFlightsRequest(origin=origin, destination=destination)
        if date is not None:
            request.date = date

        response = await client.SearchFlights(request, timeout=5)
        return MessageToDict(response)
    except grpc.RpcError as e:
        raise HTTPException(status_code=503, detail=f"gRPC error: {e.code()}")

@app.get("/flights/{id}")
async def get_flight(id: int):
    try:
        request = contract_pb2.GetFlightRequest(id=id)
        response = await client.GetFlight(request, timeout=5)
        return MessageToDict(response)
    except grpc.RpcError as e:
        raise HTTPException(status_code=503, detail=f"gRPC error: {e.code()}")

@app.post("/bookings")
async def create_booking(booking: BookingRequst):
    try:
        request = contract_pb2.GetFlightRequest(id=booking.flight_id)
        response = await client.GetFlight(request, timeout=5)

        total_price = response.flight.price * booking.seat_count

        with postgres_connection_pool.getconn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    'INSERT INTO "Booking" (flight_id, passenger_name, passenger_email, seat_count, price, status) VALUES(%s, %s, %s, %s, %s, \'CONFIRMED\') RETURNING id;', \
                    (booking.flight_id, \
                    booking.passenger_name, \
                    booking.passenger_email, \
                    booking.seat_count, \
                    total_price, \
                    )
                )
                booking_id = cur.fetchone()[0]
                request = contract_pb2.ReserveSeatsRequest(booking_id=booking_id, flight_id=booking.flight_id, seat_count=booking.seat_count)
                response = await client.ReserveSeats(request, timeout=5)

        return 200
    except grpc.RpcError as e:
        raise HTTPException(status_code=503, detail=f"gRPC error: {e.code()}")

def GetBookingFromRow(row):
    return {
        "id": row[0],
        "flight_id": row[1],
        "passenger_name": row[2],
        "passenger_email": row[3],
        "seat_count": row[4],
        "price": row[5],
        "status": row[6],
    }

@app.get("/bookings/{id}")
async def get_booking(id: int):
    with postgres_connection_pool.getconn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT * FROM "Booking" WHERE id = %s;', (id,))
            rows = cur.fetchall()
            if len(rows) != 1:
                return HTTPException(status_code=404, detail=f"Booking not found")

            return GetBookingFromRow(rows[0])

@app.get("/bookings/{id}/cancel")
async def cancel_booking(id: int):
    try:
        with postgres_connection_pool.getconn() as conn:
            with conn.cursor() as cur:
                cur.execute('UPDATE "Booking" SET status = \'CANCELLED\' WHERE id = %s;', (id,))

                request = contract_pb2.ReleaseReservationRequest(booking_id=id)
                response = await client.ReleaseReservation(request, timeout=5)

        return 200
    except grpc.RpcError as e:
        raise HTTPException(status_code=503, detail=f"gRPC error: {e.code()}")

@app.get("/bookings")
async def search_booking(user_id: str):
    with postgres_connection_pool.getconn() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM "Booking" WHERE passenger_name = %s;', (user_id,))

            return [GetBookingFromRow(row) for row in cur.fetchall()]
