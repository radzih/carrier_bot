from tgbot.misc.setup_django import setup_django; setup_django()
import datetime
import asyncio
import pytz

from tgbot.services import db
from web.app.models import *
from tgbot.handlers.search_tickets.show_routes import generate_messages, split

def find_tuestays_between(start: datetime.datetime, end: datetime.datetime) -> list:
    total_days: int = (end - start).days + 1
    sunday: int = 1
    all_days = [start + datetime.timedelta(days=day) for day in range(total_days)]
    return [day for day in all_days if day.weekday() is sunday]


def main():
    tuestays_date = find_tuestays_between(
        start=datetime.datetime.now(),
        end=datetime.datetime.now() + datetime.timedelta(weeks=5)
    )
    route = Route.objects.first()
    new_route = Route.objects.create(
        start_station=route.start_station,
        end_station=route.end_station,
        active=True,
        bus=route.bus,
        driver=route.driver,
    )
    for station in RouteStation.objects.filter(route=route):
        RouteStation.objects.create(
            station_index=station.station_index,
            station=station.station,
            route=new_route,
            departure_time=station.departure_time + datetime.timedelta(weeks=1),
        )
    
    for price in Price.objects.filter(route=route):
        Price.objects.create(
            route=new_route,
            from_station=price.from_station,
            to_station=price.to_station,
            ticket_price=price.ticket_price,
            package_price=price.package_price,
        )

main()
