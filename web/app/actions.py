import datetime

from django.contrib import admin

from . import models


@admin.action(description='Продублювати на наступний тиждень')
def duplicate_route(modeladmin, request, queryset):
    for route in queryset:
        new_route = models.Route.objects.create(
            start_station=route.start_station,
            end_station=route.end_station,
            active=route.active,
            bus=route.bus,
            driver=route.driver,
        ) 
        dublicate_prices(route, new_route)
        dublicate_route_stations(route, new_route)
        dublicate_disallowed_ways(route, new_route)


def dublicate_prices(route, new_route):
    for price in models.Price.objects.filter(route=route):
        models.Price.objects.create(
            route=new_route,
            from_station=price.from_station,
            to_station=price.to_station,
            ticket_price=price.ticket_price,
            package_price=price.package_price,
        )

    
def dublicate_route_stations(route, new_route):
    for station in models.RouteStation.objects.filter(route=route):
        models.RouteStation.objects.create(
            station_index=station.station_index,
            station=station.station,
            route=new_route,
            departure_time=station.departure_time + datetime.timedelta(weeks=1),
        )
    

def dublicate_disallowed_ways(route, new_route):
    for dis in models.DisallowedWay.objects.filter(route=route):
        models.DisallowedWay.objects.create(
            route=new_route,
            from_station = dis.from_station,
            to_station = dis.to_station,
        )
