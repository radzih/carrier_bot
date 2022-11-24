from django.dispatch import receiver
from django.db.models.signals import post_save, ModelSignal, pre_init

from ..app.models import Route, RouteStation, Price, Station


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
    )

    for i, from_station in enumerate(route_stations):
        for j, to_station in enumerate(route_stations):
            if i < j:
                if Price.objects.filter(
                    route=instance,
                    from_station=from_station.station,
                    to_station=to_station.station,
                ).exists():
                    continue
                Price.objects.create(
                    route=instance,
                    from_station=from_station.station,
                    to_station=to_station.station,
                    ticket_price=0,
                    package_price=0,
                )