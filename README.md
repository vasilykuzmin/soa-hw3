## SOA HW 3

https://dbdiagram.io/d/soa-hw3-69bac8eefb2db18e3bb06de4


### Курлы для тестов:

`sudo docker compose up --build`

`curl "http://localhost:8080/flights?origin=VKO&destination=LED&date=2026-04-01"`

`curl "http://localhost:8080/flights/1"`

`curl "http://localhost:8080/bookings/0"`

`curl "http://localhost:8080/bookings" -H "Content-Type: application/json"  -d '{"user_id": 1, "flight_id": 1, "passenger_name":"aboba", "passenger_email":"aboba@email.ru", "seat_count":3}'`

`curl "http://localhost:8080/bookings/1/cancel"`

`curl "http://localhost:8080/bookings?user_id=aboba"`
