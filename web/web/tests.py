import datetime

from django.test import TestCase
from django.db.models import Subquery, OuterRef, Func, F, Count

from web.app import models


class TestCarrier(TestCase):
    def create_towns(self):
        models.Town.objects.create(name='Town 1')
        models.Town.objects.create(name='Town 2')

    def create_stations(self):
        for town in models.Town.objects.all():
            for station in range(1, 6):
                (
                    models.Station.objects
                    .create(name=f'Station {station}', town=town)
                )
    
    def create_bus(self):
        models.Bus.objects.create(
            numbers='AA1234AA',
            seats=10,
            name='Bus 1',
            description='Bus 1 description'
        )
    
    def create_driver(self):
        models.Driver.objects.create(
            full_name='Driver 1',
            phone='+380123456789',
            telegram_id=123456789
        )
    
    
    def create_route(self):
        (
            models.Route.objects
            .create(
                start_station=(
                    models.Station.objects.first()
                ),
                end_station=(
                    models.Station.objects.last()
                ),
                active=True,
                departure_time=(
                    datetime.datetime(2022, 11, 15, 10, 0, 0)
                ),
                bus=models.Bus.objects.first(),
                driver=models.Driver.objects.first(),
                is_regular=False,
            )
        )
    
    def create_ways(self):
        stations = models.Station.objects.all()
        for index, station in enumerate(stations, 1):
            if index == len(stations):
                break
            next_station = stations[index] 
            (
                models.Way.objects
                .create(
                    station_index=index,
                    from_station=station,
                    to_station=next_station,
                )
            )
        
    def create_telegram_user(self):
        (
            models.TelegramUser.objects
            .create(
                telegram_id=123456789,
                full_name='User 1',
                phone='+380123456789',
                language='en',
            )
        )

    def create_tickets_in_fisrt_part_of_route(self):
        bus_seats = models.Bus.objects.first().seats
        stations_amount = models.Station.objects.count()
        user = models.TelegramUser.objects.first()
        for _ in range(bus_seats):
            (
                models.Ticket.objects
                .create(
                    owner=user,
                    route=(
                        models.Route
                        .objects.first()
                    ),
                    start_station=(
                        models.Station
                        .objects.first()
                    ),
                    end_station=(
                        models.Station
                        .objects
                        .all()[stations_amount // 2]
                    ),
                    is_paid=True,
                )
            )

    def create_ticket_for_all_route(self):
        bus_seats = models.Bus.objects.first().seats
        stations_amount = models.Station.objects.count()
        user = models.TelegramUser.objects.first()
        for _ in range(bus_seats):
            (
                models.Ticket.objects
                .create(
                    owner=user,
                    route=(
                        models.Route
                        .objects.first()
                    ),
                    start_station=(
                        models.Station
                        .objects
                        .first()
                    ),
                    end_station=(
                        models.Station
                        .objects.last()
                    ),
                    is_paid=True,
                )
            )
    
    def create_ticket(self, start_station_index: int, end_station_index: int):
        user = models.TelegramUser.objects.first()
        route = models.Route.objects.first()
        (
            models.Ticket.objects
            .create(
                owner=user,
                route=route,
                is_paid=True,
                start_station=(
                    models.Station
                    .objects.all()
                    [start_station_index]
                ),
                end_station=(
                    models.Station
                    .objects.all()
                    [end_station_index]
                ),
            )
        )
    
    def delete_all_tickets(self):
        for ticket in models.Ticket.objects.all():
            ticket.delete()
            
    def setUp(self) -> None:
        self.create_towns()
        self.create_stations()
        self.create_ways()
        self.create_bus()
        self.create_driver()
        self.create_route()
        self.create_telegram_user()

    def test_check_ways_amount(self):
        count_ways = models.Way.objects.count()
        right_ways = models.Station.objects.count() - 1
        self.assertEqual(count_ways, right_ways)

    def test_check_ways_order(self):
        ways = models.Way.objects.all()
        for index, way in enumerate(ways, 1):
            self.assertEqual(way.station_index, index)
    
    def test_available_seats_if_bus_is_fully(self):
        self.create_tickets_in_fisrt_part_of_route()
        route = models.Route.objects.first()
        stations_amount = models.Station.objects.count()
        calculated = []
        right = []
        for start_id in range(0, stations_amount):
            for end_id in range(start_id+1, stations_amount):
                user_start_way, user_end_way = \
                    self.get_user_start_and_end_ways(
                        user_start_station_id=start_id,
                        user_end_station_id=end_id,
                    )
                available_seats = self.get_available_seats(
                    route=route,
                    user_start_way=user_start_way,
                    user_end_way=user_end_way,
                )
                calculated.append(available_seats)
                if user_start_way.from_station.town.name == \
                    models.Town.objects.last().name:
                    right.append(10)
                else: right.append(0)
        self.assertEqual(
            calculated, right
        )

    def test_all_cases_for_tickets(self: TestCase):
        stations_amount = models.Station.objects.count()
        bus_seats = models.Bus.objects.first().seats
        route = models.Route.objects.first()
        for start_ticket_id in range(0, stations_amount):
            for end_ticket_id in range(start_ticket_id+1, stations_amount):
                self.create_ticket(
                    start_station_index=start_ticket_id,
                    end_station_index=end_ticket_id,
                )
                calculated = []
                right = []
                for start_id in range(0, stations_amount):
                    for end_id in range(start_id+1, stations_amount):
                        user_start_way, user_end_way = \
                            self.get_user_start_and_end_ways(
                                user_start_station_id=start_id,
                                user_end_station_id=end_id,
                            )
                        available_seats = self.get_available_seats(
                            route=route,
                            user_start_way=user_start_way,
                            user_end_way=user_end_way,
                        )
                        self.assertGreater(available_seats, -1)
                        calculated.append(available_seats)
                        if start_ticket_id < end_id and end_ticket_id > start_id:
                            right.append(9)
                        else:
                            right.append(10)
                        self.assertEqual(
                            available_seats,
                            right[-1],
                            msg=(
                                f'\nWrong available seats for ticket from: \n'
                                f'\t{models.Ticket.objects.all()[0].start_station} '
                                f'to {models.Ticket.objects.all()[0].end_station}\n'
                                f'and user from:\n\t{user_start_way.from_station} to {user_end_way.to_station}'
                            )
                            )
                self.delete_all_tickets()
    

    def get_user_start_and_end_ways(
        self, 
        user_start_station_id: int, 
        user_end_station_id: int,
        ) -> list[models.Way]:
        user_start_way = (
            models.Way.objects
            .get(
                from_station=(
                    models.Station
                    .objects
                    .all()[user_start_station_id]
                )
            )
        )
        user_end_way = (
            models.Way
            .objects
            .get(
                to_station=(
                    models.Station
                    .objects
                    .all()[user_end_station_id]
                )
            )
        )
        return user_start_way, user_end_way

    def get_available_seats(
        self,
        route: models.Route,
        user_start_way: models.Way,
        user_end_way: models.Way,
        ) -> int:
        seats_taken = (
            models.Ticket.objects
            .filter(route=route)
            .annotate(
                start_way_index=Subquery(
                    models.Way.objects
                    .filter(
                        from_station=OuterRef(
                            'start_station'
                        )
                    )
                    .values('station_index')
                )
            )
            .annotate(
                end_way_index=Subquery(
                    models.Way.objects
                    .filter(
                        to_station=OuterRef(
                            'end_station'
                        ),
                    )
                    .values('station_index')
                )
            )
            .annotate(
                route_end_way_index=Subquery(
                    models.Way.objects
                    .filter(
                        to_station=OuterRef(
                            'route__end_station'
                        ),
                    )
                    .values('station_index')
                )
            )
            .annotate(
                route_start_way_index=Subquery(
                    models.Way.objects
                    .filter(
                        to_station=OuterRef(
                            'route__end_station'
                        ),
                    )
                    .values('station_index')
                )
            )
            .filter(
                start_way_index__lte=user_end_way.station_index,
                end_way_index__gt=user_start_way.station_index,
            )
            .count()
        )
        return route.bus.seats - seats_taken

    
    def test_get_avaible_seats_for_all_routes(self):
        for i in models.Ticket.objects.all():
            i.delete()
        self.create_tickets_in_fisrt_part_of_route()
        user_start_way, user_end_way = \
            self.get_user_start_and_end_ways(
                user_start_station_id=6,
                user_end_station_id=9,
            )
        x = (
            models.Route.objects
            .annotate(
                taken_seats = Subquery(
                    models.Ticket.objects
                    .filter(route=OuterRef('pk'))
                    .annotate(
                        start_way_index=Subquery(
                            models.Way.objects
                            .filter(
                                from_station=OuterRef(
                                    'start_station'
                                )
                            )
                            .values('station_index')
                        )
                    )
                    .annotate(
                        end_way_index=Subquery(
                            models.Way.objects
                            .filter(
                                to_station=OuterRef(
                                    'end_station'
                                ),
                            )
                            .values('station_index')
                        )
                    )
                    .annotate(
                        route_end_way_index=Subquery(
                            models.Way.objects
                            .filter(
                                to_station=OuterRef(
                                    'route__end_station'
                                ),
                            )
                            .values('station_index')
                        )
                    )
                    .filter(
                        start_way_index__range=[1, user_end_way.station_index],
                        end_way_index__range=[user_start_way.station_index, F('route_end_way_index')],
                    )
                    .annotate(
                        count=Func(F('id'), function='Count')
                    )
                    .values_list('count', flat=True)
                )
            )
            .annotate(
                available_seats=(
                    F('bus__seats') - F('taken_seats')
                )
            )
            .values()
        )
        