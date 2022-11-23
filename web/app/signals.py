from django.dispatch import receiver
from django.db.models.signals import post_save, ModelSignal

from ..app.models import Route, RouteStation, Price


@receiver(signal=post_save, sender=Route)
def create_prices(
    signal: ModelSignal,
    sender: Route,
    instance: Route,
    raw: bool,
    using: str,
    update_fields: list,
    **kwargs,
):
    route_stations = (
        RouteStation.objects.filter(route=instance)
        .order_by('station_index')
    )

    for price in Price.objects.filter(route=instance):
        if price.from_station not in route_stations:
            price.delete()
            continue
        if price.to_station not in route_stations:
            price.delete()
            

    for i, from_station in enumerate(route_stations):
        for j, to_station in enumerate(route_stations):
            if i < j:
                Price.objects.get_or_create(
                    route=instance,
                    from_station=from_station.station,
                    to_station=to_station.station,
                    ticket_price=0,
                    package_price=0,
                )