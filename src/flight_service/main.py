import grpc
import os
from concurrent import futures
import psycopg2
from psycopg2 import pool

import contract_pb2_grpc
import contract_pb2


postgres_connection_pool = None


def GetFlightFromRow(row):
    try:
        return contract_pb2.Flight(
            id=row[0],
            flight_number=row[1],
            flight_date=row[2].isoformat(),
            company=row[3],
            origin=row[4],
            destination=row[5],
            departure_datetime=row[6].isoformat(),
            arrival_datetime=row[7].isoformat(),
            seat_capacity=row[8],
            seat_available=row[9],
            price=row[10],
            status=row[11],
        )
    except Exception as e:
        print(f'Exception: {e}', flush=True)
        raise

class FlightServiceServicer(contract_pb2_grpc.FlightServiceServicer):
    def SearchFlights(self, search_flights_request, context):
        with postgres_connection_pool.getconn() as conn:
            with conn.cursor() as cur:
                if search_flights_request.HasField('date'):
                    try:
                        cur.execute('SELECT * FROM "Flight" WHERE origin = %s AND destination = %s AND flight_date = %s AND status = \'SCHEDULED\';', (search_flights_request.origin, search_flights_request.destination, search_flights_request.date,))
                    except Exception as e:
                        print(e, flush=True)
                else:
                    cur.execute('SELECT * FROM "Flight" WHERE origin = %s AND destination = %s;', (search_flights_request.origin, search_flights_request.destination,))    
                rows = cur.fetchall()

                response = []
                for row in rows:
                    response.append(GetFlightFromRow(rows[0]))
                return contract_pb2.SearchFlightsResponse(flights=response)

    def GetFlight(self, get_flight_request, context):
        with postgres_connection_pool.getconn() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM "Flight" WHERE id = %s;', (get_flight_request.id,))
                rows = cur.fetchall()

                if len(rows) > 0:
                    return contract_pb2.GetFlightResponse(flight=GetFlightFromRow(rows[0]))
                else:
                    return None

    def ReserveSeats(self, reserve_seat_request, context):
        with postgres_connection_pool.getconn() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT seat_available FROM "Flight" WHERE id = %s;', (reserve_seat_request.flight_id,))
                rows = cur.fetchall()
                if len(rows) != 1:
                    raise 'Aboba'

                seat_available = rows[0][0]

                if reserve_seat_request.seat_count > seat_available:
                    raise 'Not enough seats!'

                cur.execute('INSERT INTO "SeatReservation" (booking_id, flight_id, seat_count, status) VALUES(%s, %s, %s, \'ACTIVE\');', (reserve_seat_request.booking_id, reserve_seat_request.flight_id, reserve_seat_request.seat_count))
                cur.execute('UPDATE "Flight" SET seat_available = seat_available - %s WHERE id = %s ;', (reserve_seat_request.seat_count, reserve_seat_request.flight_id))

                return contract_pb2.ReserveSeatsResponse()


    def ReleaseReservation(self, release_reservation_request, context):
        with postgres_connection_pool.getconn() as conn:
            with conn.cursor() as cur:
                cur.execute('UPDATE "SeatReservation" SET status = \'RELEASED\' WHERE booking_id = %s AND status = \'ACTIVE\' RETURNING flight_id, seat_count;', (release_reservation_request.booking_id,))
                row = cur.fetchone()
                flight_id = row[0]
                seat_count = row[1]
                cur.execute('UPDATE "Flight" SET seat_available = seat_available + %s WHERE id = %s ;', (seat_count, flight_id))

                return contract_pb2.ReleaseReservationResponse()


def main():
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

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    contract_pb2_grpc.add_FlightServiceServicer_to_server(FlightServiceServicer(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    main()
