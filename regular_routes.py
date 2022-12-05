import logging
import datetime
from tgbot.misc.setup_django import setup_django; setup_django()

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.db.models import OuterRef, Subquery, F
from django.utils import timezone

from web.app import models

logger = logging.getLogger(__name__)




def distinct_in_python(queryset):
    # remove dublicates in start_station end_station, route_departure_time__iso_weekday
    unique = []
    bufer = []
    for route in queryset:
        compare_list = [
            route.start_station,
            route.end_station,
            route.route_departure_time.isoweekday(),
            route.route_departure_time.hour,
        ]
        if compare_list not in bufer:
            unique.append(route)
            bufer.append(compare_list)
    return unique


def copy_routes():
    departure_time_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('pk'))
        .order_by('station_index')
        .values_list('departure_time', flat=True)[:1]
    )
    last_routes = (
        models.Route.objects
        .filter(active=True)
        .annotate(route_departure_time=departure_time_subquery)
        .order_by('-route_departure_time')
    )
    last_routes = distinct_in_python(last_routes)
    last_routes = [route 
                   for route in last_routes
                   if route.is_regular == True]
    today = timezone.now()
    in_month = today + datetime.timedelta(weeks=4, )
    for route in last_routes:
        for week in range(1, 5):
            new_route_departure_time = \
                route.route_departure_time + datetime.timedelta(weeks=week)
            if new_route_departure_time > in_month:
                new_route_departure_time = \
                route.route_departure_time + datetime.timedelta(weeks=week-1)
                week = week - 1
                break
            logger.info(f"update {route}")
        for w in range(1, week +1):
            new_route_departure_time = \
                route.route_departure_time + datetime.timedelta(weeks=w)
            new_route=models.Route.objects.create(
                start_station=route.start_station,
                end_station=route.end_station,
                bus=route.bus,
                driver=route.driver,
                is_regular=True,
                active=True,
            )
            for station in models.RouteStation.objects.filter(route=route):
                models.RouteStation.objects.create(
                    station_index=station.station_index,
                    station=station.station,
                    route=new_route,
                    departure_time=station.departure_time + datetime.timedelta(weeks=w),
                )
            
            for price in models.Price.objects.filter(route=route):
                models.Price.objects.create(
                    route=new_route,
                    from_station=price.from_station,
                    to_station=price.to_station,
                    ticket_price=price.ticket_price,
                    package_price=price.package_price,
                )
            for dis in models.DisallowedWay.objects.filter(route=route):
                models.DisallowedWay.objects.create(
                    route=new_route,
                    from_station = dis.from_station,
                    to_station = dis.to_station,
                )
 

def main():
    logging.basicConfig(
        level=logging.INFO,
        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
    )
    logger.info('Starting ')

    scheduler = BlockingScheduler()
    scheduler.add_job(
        copy_routes,
        trigger=IntervalTrigger(days=4),
    )
    scheduler.start()

       
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info('Finished')

