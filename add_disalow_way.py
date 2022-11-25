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
    route = Route.objects.get(id=route_id)
    for price in Price.objects.filter(route=route):
        if price.ticket_price == 0 and price.package_price == 0:
            DisallowedWay.objects.create(
                route=route,
                from_staion=price.from_station,
                to_station=price.to_station,
            )


main()
