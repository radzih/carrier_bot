from tgbot.misc.setup_django import setup_django; setup_django()
import datetime
import asyncio
import pytz

from django import forms
from django.utils import timezone
from tgbot.services import db
from web.app.models import *
from tgbot.handlers.search_tickets.show_routes import generate_messages, split


def main():
    route_id = int(input('Enter route id: '))
    day = int(input('Enter day: '))
    route = Route.objects.get(id=route_id)
    new_route = Route.objects.create(
        start_station=route.start_station,
        end_station=route.end_station,
        active=True,
        bus=route.bus,
        driver=route.driver,
    )
    for station in RouteStation.objects.filter(route=route):
        time = station.departure_time.astimezone(timezone.get_current_timezone())
        time = datetime.datetime(
            year=time.year,
            month=time.month,
            day=day,
            hour=time.hour,
            minute=time.minute,
            tzinfo=time.tzinfo,
        )
        RouteStation.objects.create(
            station_index=station.station_index,
            station=station.station,
            route=new_route,
            departure_time=time
        )
    
    for price in Price.objects.filter(route=route):
        Price.objects.create(
            route=new_route,
            from_station=price.from_station,
            to_station=price.to_station,
            ticket_price=price.ticket_price,
            package_price=price.package_price,
        )

    for dissallowed_way in DisallowedWay.objects.filter(route=route):
        DisallowedWay.objects.create(
            route=new_route,
            from_station=dissallowed_way.from_station,
            to_station=dissallowed_way.to_station,
        )

main()

