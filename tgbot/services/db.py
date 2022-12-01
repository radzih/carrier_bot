import datetime
import logging
import uuid

from asgiref.sync import sync_to_async

from django.db.models.functions import Concat, Lower, Upper
from django.utils import timezone
from django.db.models import F, Value, CharField, Subquery, OuterRef, Q, Count, Func, Exists, QuerySet 


from web.app import models
from web.translations import models as translations_models
from tgbot.misc import schemas

models.BusTranslation = translations_models.BusTranslation
models.TownTranslations = translations_models.TownTranslations
models.StationTranslations = translations_models.StationTranslations
models.BusOptionTranslation = translations_models.BusOptionTranslation
models.TicketTypeTranslations = translations_models.TicketTypeTranslations



@sync_to_async
def add_telegram_user(telegram_id: int, full_name: str, phone: str) -> None:
    if models.TelegramUser.objects.filter(phone=phone).exists():
        (
        models.TelegramUser.objects.filter(phone=phone)
        .update(
            telegram_id=telegram_id,
            full_name=full_name,
            language=models.Language.objects.get(code='uk'),
        )
        )
    else:
        models.TelegramUser.objects.create(
            telegram_id=telegram_id,
            full_name=full_name,
            language=models.Language.objects.get(code='uk'),
            phone=phone,
        )

@sync_to_async
def get_telegram_users() -> schemas.TelegramUser:
    return list(
        schemas.TelegramUser.parse_obj(user) \
            for user in models.TelegramUser.objects.all().prefetch_related()
    )

@sync_to_async
def is_telegram_user_registered(telegram_id: int) -> bool:
    return models.TelegramUser.objects.filter(
        telegram_id=telegram_id,
    ).exists()

@sync_to_async
def turn_notifications(telegram_id: int) -> None:
    user = models.TelegramUser.objects.get(
        telegram_id=telegram_id,
    )
    user.is_notifications_enabled = not user.is_notifications_enabled
    user.save()

@sync_to_async
def get_telegram_user(telegram_id: int) -> schemas.TelegramUser:
    return schemas.TelegramUser.parse_obj(
        (
            models.TelegramUser.objects
            .filter(telegram_id=telegram_id)
            .first()
        )
    )


@sync_to_async
def update_telegram_user_phone(telegram_id: int, phone: str) -> None:
    user = models.TelegramUser.objects.get(telegram_id=telegram_id)
    user.phone = phone
    user.save()


@sync_to_async
def search_telegram_users_by_full_name(full_name: str) -> list[schemas.TelegramUser]:
    return list(
        schemas.TelegramUser(**user) \
            for user in models.TelegramUser.objects.filter(
                full_name__icontains=full_name,
            ).values()
    )


@sync_to_async
def set_language_to_user(telegram_id: int, language_id: int) -> None:
    user = models.TelegramUser.objects.get(telegram_id=telegram_id)
    user.language = models.Language.objects.get(id=language_id)
    user.save()


@sync_to_async
def add_support_request(
    user_telegram_id: int,
    ) -> schemas.SupportRequest:
    user = models.TelegramUser.objects.get(telegram_id=user_telegram_id)
    request: models.SupportRequest = models.SupportRequest.objects.create(
        user=user,
    )
    return schemas.SupportRequest(**request.dict())


@sync_to_async
def delete_support_request(request_id) -> None:
    models.SupportRequest.objects.get(id=request_id).delete()

@sync_to_async
def get_support_request(id: int) -> schemas.SupportRequest:
    request: models.SupportRequest = models.SupportRequest.objects.get(id=id)
    return schemas.SupportRequest(**request.dict())

@sync_to_async
def update_send_message_ids_in_support_request(
    request_id: int,
    message_ids: list,
    ) -> schemas.SupportRequest:
    request: models.SupportRequest = models.SupportRequest.objects.get(id=request_id)
    request.sended_message_ids = message_ids
    request.save()
    return schemas.SupportRequest(**request.dict())

@sync_to_async
def add_operator(telegram_id: int, full_name: str) -> schemas.Operator:
    operator: models.Operator = models.Operator.objects.create(
        telegram_id=telegram_id,
        full_name=full_name,
    )
    return schemas.Operator(**operator.dict())

@sync_to_async
def delete_operator(id: int) -> schemas.Operator:
    operator: models.Operator = models.Operator.objects.get(telegram_id=id)
    operator_schema = schemas.Operator(**operator.dict())
    operator.delete()
    return operator_schema

@sync_to_async
def get_operators() -> list[schemas.Operator]:
    return list(
        schemas.Operator(**operator) \
            for operator in models.Operator.objects.all().values()
    )

@sync_to_async
def get_operator(id: int) -> schemas.Operator:
    operator: models.Operator = models.Operator.objects.get(telegram_id=id)
    return schemas.Operator(**operator.dict())

@sync_to_async
def add_operator_confirm_uuid() -> uuid.UUID:
    uuid_ = models.OperatorConfirmUUID.objects.create()
    return uuid_.uuid 

@sync_to_async
def delete_operator_confirm_uuid(uuid_: uuid.UUID) -> None:
    models.OperatorConfirmUUID.objects.get(uuid=uuid_).delete()

@sync_to_async
def get_all_operator_confirm_uuids() -> list[uuid.UUID]:
    return list(
        uuid_.uuid \
            for uuid_ in models.OperatorConfirmUUID.objects.all()
    )
# Station functions -----------------------------------------------------------
@sync_to_async
def get_stations_by_name(name: str) -> list[schemas.Station]:
    return list(
        schemas.Station.parse_obj(station) \
            for station in (
                models.Station.objects
                .annotate(
                    full_name=Concat(
                        F('town__name'),
                        Value('-'),
                        'name',
                        output_field=CharField(),
                    )
                )
                .filter(full_name__icontains=name)
                .order_by('full_name')
            )
    )

@sync_to_async
def get_station(
    station_id: int,
    telegram_id: int,
) -> schemas.Station:
    user = models.TelegramUser.objects.get(telegram_id=telegram_id)
    station = models.Station.objects.get(id=station_id)
    station.name = models.StationTranslations.objects.get(
        station=station,
        language=user.language,
    ).translation
    station.town.name = models.TownTranslations.objects.get(
        town=station.town,
        language=user.language,
    ).translation
    return schemas.Station.parse_obj(
        station
    )

@sync_to_async
def get_user_ticket_stations_history(telegram_id: int) -> list[schemas.Station]:
    user = models.TelegramUser.objects.get(telegram_id=telegram_id)
    ticket_with_station_subquery = Subquery(
        models.Ticket.objects
        .filter(owner=user)
        .filter(
            Q(start_station=OuterRef('id')) | Q(end_station=OuterRef('id'))
            )
    )
    user_station_history = (
        models.Station.objects
        .annotate(is_in_user_ticket=Exists(ticket_with_station_subquery))
        .filter(is_in_user_ticket=True)
    )
    return list(
        schemas.Station.parse_obj(station) \
            for station in user_station_history[:5]
    )

@sync_to_async
def get_user_package_stations_history(telegram_id: int) -> list[schemas.Station]:
    package_with_station_subquery = Subquery(
        models.Package.objects
        .filter(owner=telegram_id)
        .filter(
            Q(start_station=OuterRef('id')) | Q(end_station=OuterRef('id'))
            )
    )
    user_station_history = (
        models.Station.objects
        .annotate(is_in_user_package=Exists(package_with_station_subquery))
        .filter(is_in_user_package=True)
    )
    return list(
        schemas.Station.parse_obj(station) \
            for station in user_station_history
    )


# ------------------------------------------------------------Station functions

    
@sync_to_async
def update_chosen_route_data(
    telegram_id: int,
    **kwargs,
) -> schemas.ChosenRouteData:
    departure_time_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('route'))
        .filter(station=OuterRef('from_station'))
        .values('departure_time')
    )
    chosen_route_data = (
        models.ChosenRouteData.
        objects.filter(user=telegram_id)
        .annotate(departure_time=departure_time_subquery)
    )
    
    chosen_route_data.update(**kwargs)
    return schemas.ChosenRouteData.parse_obj(chosen_route_data.first())

@sync_to_async
def create_or_clean_chosen_route_data(
    telegram_id: int
    ) -> schemas.ChosenRouteData:
    chosen_route_data = (
        models.ChosenRouteData.
        objects.filter(user=telegram_id).delete()
    )
    chosen_route_data = models.ChosenRouteData.objects.create(
        user_id=telegram_id,
        )
    return schemas.ChosenRouteData.parse_obj(chosen_route_data)

@sync_to_async
def get_chosen_route_data(telegram_id: int) -> schemas.ChosenRouteData:
    package_price_subquery = Subquery(
        models.Price.objects
        .filter(route=OuterRef('route'))
        .filter(from_station=OuterRef('from_station'))
        .filter(to_station=OuterRef('to_station'))
        .values('package_price')
    )
    ticket_price_subquery = Subquery(
        models.Price.objects
        .filter(route=OuterRef('route'))
        .filter(from_station=OuterRef('from_station'))
        .filter(to_station=OuterRef('to_station'))
        .values('ticket_price')
    )
    departure_time_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('route'))
        .filter(station=OuterRef('from_station'))
        .values('departure_time')
    )
    chosen_route_data = (
        models.ChosenRouteData.
        objects.filter(user=telegram_id)
        .annotate(
            package_price=package_price_subquery,
            ticket_price=ticket_price_subquery,
            departure_time=departure_time_subquery,
            )
    )
    return schemas.ChosenRouteData.parse_obj(chosen_route_data.first())
    

# @sync_to_async
# def get_user_ticket_choose_data(telegram_id: int) -> schemas.UserTicketChooseData:
#     user: models.TelegramUser = (
#         models.TelegramUser.objects.get(telegram_id=telegram_id)
#     )
#     ticket_data: models.UserTicketChooseData = (
#         models.UserTicketChooseData.objects.get(user=user)
#     )
#     return schemas.UserTicketChooseData.parse_obj(ticket_data)


@sync_to_async
def get_routes_with_available_seats() -> list[schemas.Route]:
    routes = (
        models.Route.objects
        .annotate(route_start_station_index=1)
        .annotate(
            route_end_station_index=Subquery(
                models.RouteStation.objects
                .filter(route=OuterRef('pk'))
                .count()
            )
        )
        .annotate(
            taken_seats=Subquery(
                models.Ticket.objects
                .annotate(
                    ticket_start_station_index=Subquery(
                        models.RouteStation.objects
                        .filter(route=OuterRef('route'))
                        .filter(
                            station=OuterRef('start_station'),
                        )
                    )
                )
                .annotate(
                    ticket_end_station_index=Subquery(
                        models.RouteStation.objects
                        .filter(route=OuterRef('route'))
                        .filter(
                            station=OuterRef('end_station'),
                        )
                    )
                )
            )
        )
    )

# Ticket funcions ------------------------

@sync_to_async
def book_ticket(
    route_id: int,
    start_station_id: int,
    end_station_id: int,
    telegram_id: int,
    passenger: schemas.Person,
    type_id: int,
): 
    user = models.TelegramUser.objects.get(telegram_id=telegram_id)
    person = models.Person.objects.filter(name=passenger.name, surname=passenger.surname, telegram_user=user).first()
    if not person:
        person = models.Person.objects.create(
                name=passenger.name,
                surname=passenger.surname,
                telegram_user=user,
            )

    ticket = models.Ticket.objects.create(
        owner=user,
        route_id=route_id,
        start_station_id=start_station_id,
        end_station_id=end_station_id,
        passenger=person,
        type_id=type_id,
        is_paid=False,
        is_booked=True,
    )
    ticket.departure_time = (
        models.RouteStation.objects
        .filter(route_id=route_id)
        .filter(station_id=start_station_id)
        .first()
        .departure_time
    )
    ticket.start_station.name = (
        models.StationTranslations.objects
        .filter(station_id=start_station_id)
        .filter(language=user.language)
        .first()
        .translation
    )
    ticket.start_station.town.name = (
        models.TownTranslations.objects
        .filter(town_id=ticket.start_station.town.id)
        .filter(language=user.language)
        .first()
        .translation
    )
    ticket.end_station.name = (
        models.StationTranslations.objects
        .filter(station_id=end_station_id)
        .filter(language=user.language)
        .first()
        .translation
    )
    ticket.end_station.town.name = (
        models.TownTranslations.objects
        .filter(town_id=ticket.end_station.town.id)
        .filter(language=user.language)
        .first()
        .translation
    )
    ticket.type.name = (
        models.TicketTypeTranslations.objects
        .get(ticket_type_id=type_id, language=user.language)
        .translation
    )
    price = (
        models.Price.objects
        .filter(route_id=route_id)
        .filter(from_station_id=start_station_id)
        .filter(to_station_id=end_station_id)
        .first()
        .ticket_price 
    ) 
    ticket.price = price
    return schemas.Ticket.parse_obj(ticket)

@sync_to_async
def get_ticket(ticket_id: int) -> schemas.Ticket:
    departure_time_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('route'))
        .filter(station=OuterRef('start_station'))
        .values('departure_time')
    )
    arrival_time_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('route'))
        .filter(station=OuterRef('end_station'))
        .values('departure_time')
    )
    ticket = (
        models.Ticket.objects
        .filter(id=ticket_id)
        .annotate(departure_time=departure_time_subquery)
        .annotate(arrival_time=arrival_time_subquery)
        .first()
        )
    price = (
        models.Price.objects
        .filter(route=ticket.route)
        .filter(from_station=ticket.start_station)
        .filter(to_station=ticket.end_station)
        .first()
        .ticket_price
    )
    ticket.price = price 
    return schemas.Ticket.parse_obj(ticket)


@sync_to_async
def is_ticket_exists(ticket_id: int) -> bool:
    return models.Ticket.objects.filter(id=ticket_id).exists()


@sync_to_async
def mark_ticket_as_paid(ticket_id: int, payment_id: int) -> schemas.Ticket:
    (
        models.Ticket.objects
        .filter(id=ticket_id)
        .update(
            is_paid=True,
            is_booked=False,
            payment_id=payment_id,
            paid_time=timezone.now(),
        )
    )
    ticket = models.Ticket.objects.get(id=ticket_id)
    return schemas.Ticket.parse_obj(ticket)

@sync_to_async
def mark_ticket_as_pay_in_bus(ticket_id: int) -> schemas.Ticket:
    (
        models.Ticket.objects
        .filter(id=ticket_id)
        .update(
            is_paid=False,
            is_booked=False,
        )
    )
    ticket = models.Ticket.objects.get(id=ticket_id)
    return schemas.Ticket.parse_obj(ticket)

@sync_to_async
def delete_ticket(ticket_id: int) -> schemas.Ticket:
    ticket = models.Ticket.objects.get(id=ticket_id)
    ticket_schema = schemas.Ticket.parse_obj(ticket)
    ticket.delete()
    return ticket_schema

@sync_to_async
def get_ticket_types(telegram_id: int) -> list[schemas.TicketType]:
    user = models.TelegramUser.objects.get(telegram_id=telegram_id)
    ticket_types = (
        models.TicketType.objects
        .all()
    )
    for ticket_type in ticket_types:
        ticket_type.name = (
        models.TicketTypeTranslations.objects
        .filter(language=user.language)
        .filter(ticket_type=ticket_type)
        .first()
        .translation
    )
    return list(
        schemas.TicketType.parse_obj(ticket_type)
        for ticket_type in ticket_types
    )

@sync_to_async
def get_tickets_with_unique_passengers(
    telegram_id: int,
) -> list[schemas.Ticket]:
    ticket_with_unique_fio = (
        models.Ticket.objects
        .filter(owner=telegram_id)
        .annotate(pib=Concat('passenger_name', Value(' '), 'passenger_surname'))
        .distinct('pib')
    )
    return list(
        schemas.Ticket.parse_obj(ticket)
        for ticket in ticket_with_unique_fio
    )


@sync_to_async
def get_user_valid_tickets(telegram_id: int):
    user = models.TelegramUser.objects.get(telegram_id=telegram_id)
    departure_time_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('route'))
        .filter(station=OuterRef('start_station'))
        .values('departure_time')
    )
    arrival_time_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('route'))
        .filter(station=OuterRef('end_station'))
        .values('departure_time')
    )
    price_subquery = Subquery(
        models.Price.objects
        .filter(route=OuterRef('route'))
        .filter(from_station=OuterRef('start_station'))
        .filter(to_station=OuterRef('end_station'))
        .values('ticket_price')
    )
    tickets = (
        models.Ticket.objects
        .filter(owner=user)
        .annotate(departure_time=departure_time_subquery)
        .annotate(arrival_time=arrival_time_subquery)
        .annotate(price=price_subquery)
        .filter(departure_time__gte=timezone.now())
        .filter(is_booked=False)
        .order_by('departure_time')
    )
    # for ticket in tickets:
    #     translage_station(ticket.start_station, user)
    #     translage_station(ticket.end_station, user)
    return list(
        schemas.Ticket.parse_obj(ticket)
        for ticket in tickets
    )


@sync_to_async
def get_user_archive_tickets(telegram_id: int) -> list[schemas.Ticket]:
    user = models.TelegramUser.objects.get(telegram_id=telegram_id)
    departure_time_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('route'))
        .filter(station=OuterRef('start_station'))
        .values('departure_time')
    )
    arrival_time_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('route'))
        .filter(station=OuterRef('end_station'))
        .values('departure_time')
    )
    tickets = (
        models.Ticket.objects
        .filter(owner=user)
        .annotate(departure_time=departure_time_subquery)
        .annotate(arrival_time=arrival_time_subquery)
        .filter(departure_time__lte=timezone.now())
        .order_by('departure_time')
    )
    return list(
        schemas.Ticket.parse_obj(ticket)
        for ticket in tickets
    )   
# ------------------------ Ticket funcions 

# Route functions ------------------------

@sync_to_async
def get_route(
    start_station_code: str,
    end_station_code: str,
    route_code: str,
) -> schemas.Route:
    user_start_station_index_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('pk'))
        .filter(station__code=start_station_code)
        .values('station_index')
    )
    user_end_station_index_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('pk'))
        .filter(station__code=end_station_code)
        .values('station_index')
        )
    departure_time_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('pk'))
        .filter(station__code=start_station_code)
        .values('departure_time')
    )
    arrival_time_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('pk'))
        .filter(station__code=end_station_code)
        .values('departure_time')
    )
    route_end_station_index_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('pk'))
        .filter(station=OuterRef('end_station'))
        .values('station_index')
    )
    ticket_start_station_index_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('route'))
        .filter(station=OuterRef('start_station'))
        .values('station_index')
    )
    ticket_end_station_index_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('route'))
        .filter(station=OuterRef('end_station'))
        .values('station_index')
    )
    seats_taken_subquery = Subquery(
        models.Ticket.objects
        .annotate(
            ticket_start_station_index=ticket_start_station_index_subquery,
            ticket_end_station_index=ticket_end_station_index_subquery,
        )
        .filter(
            ticket_start_station_index__lte=OuterRef('user_end_station_index'),
            ticket_end_station_index__gt=OuterRef('user_start_station_index'),
            route=OuterRef('pk'),
        )
        .annotate(count=Func(F('id'), function='Count'))
        .values('count')
    )
    get_available_seats = (
        F('bus__seats') - F('seats_taken')
    )
    beneficiary_count_subquery = Subquery(
        models.Ticket.objects
        .filter(route=OuterRef('pk'))
        .exclude(type__name='Дорослий')
        .annotate(count=Func(F('id'), function='Count'))
        .values('count')
    )
    route = (
        models.Route.objects
        .annotate(
            user_start_station_index=user_start_station_index_subquery,
            user_end_station_index=user_end_station_index_subquery,
            route_start_station_index=Value(1),
            route_end_station_index=route_end_station_index_subquery,
            departure_time=departure_time_subquery,
            arrival_time=arrival_time_subquery,
            seats_taken=seats_taken_subquery,
            available_seats=get_available_seats,
            beneficiary_count=beneficiary_count_subquery,
        )
        .filter(user_start_station_index__lt=F('user_end_station_index'))
        .filter(available_seats__gt=0)
        .filter(active=True)
        .filter(code=route_code)
        .first()
    )
    route.user_start_station = models.Station.objects.get(code=start_station_code)
    route.user_end_station = models.Station.objects.get(code=end_station_code)
    return schemas.Route.parse_obj(route)

@sync_to_async
def is_route_started(
    route_id: int,
    from_station_id: int,
) -> bool:
    departure_time_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('pk'))
        .filter(station=from_station_id)
        .values('departure_time')
    )
    return bool(
        models.Route.objects
        .filter(id=route_id)
        .annotate(
            departure_time=departure_time_subquery,
        )
        .filter(departure_time__lte=timezone.now())
        .first()
    )
    
@sync_to_async
def get_routes_with_user_route_data(telegram_id: int) -> list[schemas.Route]:
    chosen_route_data: models.ChosenRouteData = (
        models.ChosenRouteData.objects.
        filter(user=telegram_id).first()
    )
    user_start_station_index_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('pk'))
        .filter(station=chosen_route_data.from_station)
        .values('station_index')
    )
    user_end_station_index_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('pk'))
        .filter(station=chosen_route_data.to_station)
        .values('station_index')
        )
    departure_time_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('pk'))
        .filter(station=chosen_route_data.from_station)
        .values('departure_time')
    )
    arrival_time_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('pk'))
        .filter(station=chosen_route_data.to_station)
        .values('departure_time')
    )
    is_allowed_subquery = Exists(
        Subquery(
            models.DisallowedWay.objects
            .filter(from_station=chosen_route_data.from_station)
            .filter(to_station=chosen_route_data.to_station)
        ),
        negated=True,
    )
    package_price_subquery = Subquery(
        models.Price.objects
        .filter(route=OuterRef('pk'))
        .filter(from_station=chosen_route_data.from_station)
        .filter(to_station=chosen_route_data.to_station)
        .values('package_price')
    )
    routes = (
        models.Route.objects
        .annotate(
            user_start_station_index=user_start_station_index_subquery,
            user_end_station_index=user_end_station_index_subquery,
            departure_time=departure_time_subquery,
            arrival_time=arrival_time_subquery,
            is_allowed=is_allowed_subquery,
            package_price=package_price_subquery,
        )
        .filter(user_start_station_index__lt=F('user_end_station_index'))
        .filter(is_allowed=True)
        .filter(departure_time__gt=timezone.now())
        .filter(departure_time__lt=timezone.now()+datetime.timedelta(weeks=3))
    )
    return list(schemas.Route.parse_obj(route) for route in routes)

@sync_to_async
def get_routes_from_to_with_available_seats(
    start_station_id: int,
    end_station_id: int,
) -> list[schemas.Route]:
    user_start_station_index_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('pk'))
        .filter(station=start_station_id)
        .values('station_index')
    )
    user_end_station_index_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('pk'))
        .filter(station=end_station_id)
        .values('station_index')
        )
    departure_time_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('pk'))
        .filter(station=end_station_id)
        .values('departure_time')
    )
    arrival_time_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('pk'))
        .filter(station=end_station_id)
        .values('departure_time')
    )
    is_allowed_subquery = Exists(
        Subquery(
            models.DisallowedWay.objects
            .filter(from_station=start_station_id)
            .filter(to_station=end_station_id)
        ),
        negated=True,
    )
    ticket_price_subquery = Subquery(
        models.Price.objects
        .filter(route=OuterRef('pk'))
        .filter(from_station=start_station_id)
        .filter(to_station=end_station_id)
        .values('ticket_price')
    )
    route_end_station_index_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('pk'))
        .filter(station=OuterRef('end_station'))
        .values('station_index')
    )
    ticket_start_station_index_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('route'))
        .filter(station=OuterRef('start_station'))
        .values('station_index')
    )
    ticket_end_station_index_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('route'))
        .filter(station=OuterRef('end_station'))
        .values('station_index')
    )
    seats_taken_subquery = Subquery(
        models.Ticket.objects
        .annotate(
            ticket_start_station_index=ticket_start_station_index_subquery,
            ticket_end_station_index=ticket_end_station_index_subquery,
        )
        .filter(
            route=OuterRef('pk'),
            ticket_start_station_index__lte=OuterRef('user_end_station_index'),
            ticket_end_station_index__gt=OuterRef('user_start_station_index'),
        )
        .annotate(count=Func(F('id'), function='Count'))
        .values('count')
    )
    get_available_seats = (
        F('bus__seats') - F('seats_taken')
    )
    user_departure_time_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('pk'))
        .filter(station=start_station_id)
        .values('departure_time')
    )
    routes = (
        models.Route.objects
        .annotate(
            user_start_station_index=user_start_station_index_subquery,
            user_end_station_index=user_end_station_index_subquery,
            route_start_station_index=Value(1),
            route_end_station_index=route_end_station_index_subquery,
            departure_time=departure_time_subquery,
            arrival_time=arrival_time_subquery,
            is_allowed=is_allowed_subquery,
            ticket_price=ticket_price_subquery,
            seats_taken=seats_taken_subquery,
            available_seats=get_available_seats,
            user_departure_time=user_departure_time_subquery,
        )
        .filter(user_start_station_index__lt=F('user_end_station_index'))
        .filter(available_seats__gt=0)
        .filter(is_allowed=True)
        .filter(active=True)
        .filter(departure_time__gt=timezone.now())
    )
    return list(schemas.Route.parse_obj(route) for route in routes)


@sync_to_async
def get_routes_from_to_in_date(
    start_station_id: int,
    end_station_id: int,
    date: datetime.date,
    telegram_id: int
):
    user = models.TelegramUser.objects.get(telegram_id=telegram_id)
    user_start_station_index_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('pk'))
        .filter(station=start_station_id)
        .values('station_index')
    )
    user_end_station_index_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('pk'))
        .filter(station=end_station_id)
        .values('station_index')
        )
    departure_time_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('pk'))
        .filter(station=start_station_id)
        .values('departure_time')
    )
    arrival_time_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('pk'))
        .filter(station=end_station_id)
        .values('departure_time')
    )
    is_allowed_subquery = Exists(
        Subquery(
            models.DisallowedWay.objects
            .filter(from_station=start_station_id)
            .filter(to_station=end_station_id)
        ),
        negated=True,
    )
    ticket_price_subquery = Subquery(
        models.Price.objects
        .filter(route=OuterRef('pk'))
        .filter(from_station=start_station_id)
        .filter(to_station=end_station_id)
        .values('ticket_price')
    )
    package_price_subquery = Subquery(
        models.Price.objects
        .filter(route=OuterRef('pk'))
        .filter(from_station=start_station_id)
        .filter(to_station=end_station_id)
        .values('package_price')
    )
    route_end_station_index_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('pk'))
        .filter(station=OuterRef('end_station'))
        .values('station_index')
    )
    ticket_start_station_index_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('route'))
        .filter(station=OuterRef('start_station'))
        .values('station_index')
    )
    ticket_end_station_index_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('route'))
        .filter(station=OuterRef('end_station'))
        .values('station_index')
    )
    seats_taken_subquery = Subquery(
        models.Ticket.objects
        .annotate(
            ticket_start_station_index=ticket_start_station_index_subquery,
            ticket_end_station_index=ticket_end_station_index_subquery,
        )
        .filter(
            ticket_start_station_index__lte=OuterRef('user_end_station_index'),
            ticket_end_station_index__gt=OuterRef('user_start_station_index'),
            route=OuterRef('pk'),
        )
        .annotate(count=Func(F('id'), function='Count'))
        .values('count')
    )
    get_available_seats = (
        F('bus__seats') - F('seats_taken')
    )
    beneficiary_count_subquery = Subquery(
        models.Ticket.objects
        .filter(route=OuterRef('pk'))
        .exclude(type__name='Дорослий')
        .annotate(count=Func(F('id'), function='Count'))
        .values('count')
    )
    routes = (
        models.Route.objects
        .annotate(
            user_start_station_index=user_start_station_index_subquery,
            user_end_station_index=user_end_station_index_subquery,
            route_start_station_index=Value(1),
            route_end_station_index=route_end_station_index_subquery,
            departure_time=departure_time_subquery,
            arrival_time=arrival_time_subquery,
            is_allowed=is_allowed_subquery,
            ticket_price=ticket_price_subquery,
            pack_price=package_price_subquery,
            seats_taken=seats_taken_subquery,
            available_seats=get_available_seats,
            beneficiary_count=beneficiary_count_subquery,
        )
        .filter(user_start_station_index__lt=F('user_end_station_index'))
        .filter(available_seats__gt=0)
        .filter(is_allowed=True)
        .filter(active=True)
        .filter(departure_time__year=date.year)
        .filter(departure_time__month=date.month)
        .filter(departure_time__day=date.day)
    )[:10]
    user_start_station = models.Station.objects.get(pk=start_station_id)
    user_end_station = models.Station.objects.get(pk=end_station_id)
    translage_station(user_start_station, user)
    translage_station(user_end_station, user)
    for route in routes:
        route.user_start_station = user_start_station
        route.user_end_station = user_end_station
        route.user_departure_time = (
            models.RouteStation.objects
            .filter(route=route)
            .filter(station=start_station_id)
            .first().departure_time
        )
        route.user_arrival_time = (
            models.RouteStation.objects
            .filter(route=route)
            .filter(station=end_station_id)
            .first().departure_time
        )
    return list(schemas.Route.parse_obj(route) for route in routes)



# ------------------------ Route functions

def translage_station(station, user):
    station.name = models.StationTranslations.objects.get(
        station=station,
        language=user.language,
    ).translation
    station.town.name = models.TownTranslations.objects.get(
        town=station.town,
        language=user.language,
    ).translation
    return station

# Package functions ------------------------

@sync_to_async
def create_package(
    telegram_id: int,
    route_id: int,
    start_station_id: int,
    sender_full_name: str,
    sender_phone_number: str,
    receiver_full_name: str,
    receiver_phone_number: str,
    end_station_id: int,
    is_paid: bool,
    payment_id: str | None = None, 
) -> schemas.Package:
    user = models.TelegramUser.objects.get(telegram_id=telegram_id)
    package_id = (
        models.Package.objects
        .create(
            owner=user,
            route_id=route_id,
            start_station_id=start_station_id,
            end_station_id=end_station_id,
            is_paid=is_paid,
            sender=models.Person.objects.get_or_create(
                name=sender_full_name.split()[0],
                surname=sender_full_name.split()[1],
                phone=sender_phone_number,
                telegram_user=user,
            )[0],
            receiver=models.Person.objects.get_or_create(
                name=receiver_full_name.split()[0],
                surname=receiver_full_name.split()[1],
                phone=receiver_phone_number,
                telegram_user=user,
            )[0],
            payment_id=payment_id,
            paid_time=timezone.now(),
        )
        .id
    )
    return package_id


@sync_to_async
def get_packages_with_unique_senders(
    telegram_id: int,
) -> list[schemas.Package]:
    packages_with_unique_pib = (
        models.Package.objects
        .filter(owner=telegram_id)
        .annotate(pib=Concat('sender_name', Value(' '), 'sender_surname'))
        .distinct('pib')
    )
    return list(
        schemas.Package.parse_obj(package)
        for package in packages_with_unique_pib
    )

@sync_to_async
def get_packages_with_unique_receivers(
    telegram_id: int,
) -> list[schemas.Package]:
    packages_with_unique_pib = (
        models.Package.objects
        .filter(owner=telegram_id)
        .annotate(pib=Concat('receiver_name', Value(' '), 'receiver_surname'))
        .distinct('pib')
    )
    return list(
        schemas.Package.parse_obj(package)
        for package in packages_with_unique_pib
    )


@sync_to_async
def get_package(id: int) -> schemas.Package:
    departure_time_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('route'))
        .filter(station=OuterRef('start_station'))
        .values('departure_time')
    )
    arrival_time_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('route'))
        .filter(station=OuterRef('end_station'))
        .values('departure_time')
    )
    price_subquery = Subquery(
        models.Price.objects
        .filter(route=OuterRef('route'))
        .filter(from_station=OuterRef('start_station'))
        .filter(to_station=OuterRef('end_station'))
        .values('package_price')
    )   
    package = (
        models.Package.objects.filter(id=id)
        .annotate(
            price=price_subquery,
            arrival_time=arrival_time_subquery,
            departure_time=departure_time_subquery,
        )
        .first()
    )
    return schemas.Package.parse_obj(package)


@sync_to_async
def get_user_valid_packages(telegram_id: int) -> list[schemas.Package]:
    user = models.TelegramUser.objects.get(telegram_id=telegram_id)
    departure_time_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('route'))
        .filter(station=OuterRef('start_station'))
        .values('departure_time')
    )
    arrival_time_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('route'))
        .filter(station=OuterRef('end_station'))
        .values('departure_time')
    )
    price_subquery = Subquery(
        models.Price.objects
        .filter(route=OuterRef('route'))
        .filter(from_station=OuterRef('start_station'))
        .filter(to_station=OuterRef('end_station'))
        .values('package_price')
    )
    packages = (
        models.Package.objects
        .filter(owner=user)
        .annotate(departure_time=departure_time_subquery)
        .annotate(arrival_time=arrival_time_subquery)
        .filter(departure_time__gte=timezone.now())
        .annotate(price=price_subquery)
        .order_by('departure_time')
    )
    return list(
        schemas.Package.parse_obj(package)
        for package in packages
    )


@sync_to_async
def delete_package(id: int) -> None:
    models.Package.objects.filter(id=id).delete()


@sync_to_async
def get_user_archive_packages(telegram_id: int) -> list[schemas.Package]:
    user = models.TelegramUser.objects.get(telegram_id=telegram_id)
    departure_time_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('route'))
        .filter(station=OuterRef('start_station'))
        .values('departure_time')
    )
    arrival_time_subquery = Subquery(
        models.RouteStation.objects
        .filter(route=OuterRef('route'))
        .filter(station=OuterRef('end_station'))
        .values('departure_time')
    )
    price_subquery = Subquery(
        models.Price.objects
        .filter(route=OuterRef('route'))
        .filter(from_station=OuterRef('start_station'))
        .filter(to_station=OuterRef('end_station'))
        .values('package_price')
    )
    packages = (
        models.Package.objects
        .filter(owner=user)
        .annotate(departure_time=departure_time_subquery)
        .annotate(arrival_time=arrival_time_subquery)
        .filter(departure_time__lte=timezone.now())
        .annotate(price=price_subquery)
        .order_by('departure_time')
    )
    return list(
        schemas.Package.parse_obj(package)
        for package in packages
    )   

# ------------------------ Package functions

# Language functions ------------------------

@sync_to_async
def get_languages() -> list[schemas.Language]:
    languages = models.Language.objects.all()
    return list(
        schemas.Language.parse_obj(language)
        for language in languages
    )

# ------------------------ Language functions

# UserSearchStationHistory functions ------------------------ 

@sync_to_async
def add_start_station_to_users_search_history(
    telegram_id: int,
    station_id: int,
) -> None:
    user = models.TelegramUser.objects.get(telegram_id=telegram_id)
    models.UserStartStationHistory.objects.get_or_create(
        user=user,
        station_id=station_id,
    )


@sync_to_async
def add_end_station_to_users_search_history(
    telegram_id: int,
    station_id: int,
) -> None:
    user = models.TelegramUser.objects.get(telegram_id=telegram_id)
    models.UserEndStationHistory.objects.get_or_create(
        user=user,
        station_id=station_id,
    )


@sync_to_async
def get_user_search_start_station_history(
    telegram_id: int,
) -> list[schemas.Station]:
    user = models.TelegramUser.objects.get(telegram_id=telegram_id)
    records = (
        models.UserStartStationHistory.objects
        .filter(user__telegram_id=telegram_id)
        .order_by('-id')
    )
    for record in records:
        record.station.name = models.StationTranslations.objects.get(
            language=user.language,
            station=record.station,
        ).translation
        record.station.town.name = models.TownTranslations.objects.get(
            language=user.language,
            town=record.station.town,
        ).translation
            
    return list(
        schemas.Station.parse_obj(record.station)
        for record in records
    )


@sync_to_async
def get_user_search_end_station_history(
    telegram_id: int,
) -> list[schemas.Station]:
    user = models.TelegramUser.objects.get(telegram_id=telegram_id)
    records = (
        models.UserEndStationHistory.objects
        .filter(user=user)
        .order_by('-id')
    )
    for record in records:
        record.station.name = models.StationTranslations.objects.get(
            language=user.language,
            station=record.station,
        ).translation
        record.station.town.name = models.TownTranslations.objects.get(
            language=user.language,
            town=record.station.town,
        ).translation
        
    return list(
        schemas.Station.parse_obj(record.station)
        for record in records
    )

# ------------------------ UserSearchStationHistory functions

# StationLanguage functions ------------------------


@sync_to_async
def search_station_by_name(
    name: str,
    telegram_id: int
) -> list[schemas.Station]:
    user = models.TelegramUser.objects.get(telegram_id=telegram_id)
    
    records = (
        models.Station.objects
        .annotate(
            station__name=Subquery(
                models.StationTranslations.objects
                .filter(language=user.language)
                .filter(station=OuterRef('id'))
                .values('translation')
            ),
        )
        .annotate(
            town__name=Subquery(
                models.TownTranslations.objects
                .filter(language=user.language)
                .filter(town=OuterRef('town'))
                .values('translation')
            )
        )
        .annotate(
            full_name=Concat(F('station__name'), Value('-'), F('town__name'))
        )
        .filter(full_name__icontains=name)
    )    

    for record in records:
        record.name = record.station__name
        record.town.name = record.town__name
    return list(
        schemas.Station.parse_obj(record)
        for record in records
    )

# ------------------------ StationLanguage functions

# RouteStation functions ------------------------

@sync_to_async
def get_route_from_to_stations(
    start_station_code: str,
    end_station_code: str,
    route_code: str, 
    telegram_id: int,
) -> list[schemas.Station]:
    user = models.TelegramUser.objects.get(telegram_id=telegram_id)
    route_stations = (
        models.RouteStation.objects
        .filter(route__code=route_code)
        .filter(station_index__gte=Subquery(
            models.RouteStation.objects
            .filter(route__code=route_code)
            .filter(station__code=start_station_code)
            .values('station_index')
            )
        )
        .filter(station_index__lte=Subquery(
            models.RouteStation.objects
            .filter(route__code=route_code)
            .filter(station__code=end_station_code)
            .values('station_index')
            )
        )
        .order_by('station_index')
    )
    stations = []
    for route_station in route_stations:
        route_station.station.departure_time = route_station.departure_time
        translage_station(route_station.station, user)
        stations.append(route_station.station)
    return list(
        schemas.Station.parse_obj(station)
        for station in stations
    )


# ------------------------ RouteStation functions


# Bus functions ------------------------

@sync_to_async
def get_bus(
    bus_code: str,
    telegram_id: int,
):
    user = models.TelegramUser.objects.get(telegram_id=telegram_id)
    bus = models.Bus.objects.get(code=bus_code)
    translated_bus = models.BusTranslation.objects.get(
        language=user.language,
        bus=bus,
    )
    bus.name = translated_bus.name_translation
    bus.description = translated_bus.description_translation
    translated_options = []
    for option in bus.options.all():
        translated_option = models.BusOptionTranslation.objects.get(
            language=user.language,
            bus_option=option,
        )
        option.name = translated_option.translation
        translated_options.append(
            option
        )

    bus.options.set(translated_options)
    return schemas.Bus.parse_obj(bus)

    

@sync_to_async
def get_popular_stations(
    telegram_id: int,
) -> list[schemas.Station]:
    user = models.TelegramUser.objects.get(telegram_id=telegram_id)
    stations = (
        models.Station.objects
        .filter(is_popular=True)
    )
    for station in stations:
        translage_station(station, user)
        translage_station(station, user)
    return list(
        schemas.Station.parse_obj(station)
        for station in stations
    )
        


# ------------------------ Bus functions

@sync_to_async
def get_quick_answers() -> list[schemas.QuickAnswer]:
    return [
        schemas.QuickAnswer.parse_obj(answer)
        for answer in models.QuickAnswers.objects.all()]