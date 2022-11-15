import datetime
import logging
import math
from typing import Any, Optional, Type
import uuid
from django.utils import timezone

from pydantic import BaseModel, validator


class Language(BaseModel):
    id: int
    code: str
    name: str

    @classmethod
    def parse_obj(cls, obj: Any) -> 'Language':
        return Language(code=obj.code, name=obj.name, id=obj.id)


class TelegramUser(BaseModel):
    telegram_id: int
    full_name: str
    join_time: datetime.datetime
    language: Language
    phone: Optional[str] = None
    is_notifications_enabled: bool = True
    
    @classmethod
    def parse_obj(cls: Type['TelegramUser'], obj: Any) -> 'TelegramUser':
        cls.update_forward_refs()
        object_ = cls(
            telegram_id=obj.telegram_id,
            full_name=obj.full_name,
            join_time=obj.join_time,
            language=Language.parse_obj(obj.language),
            phone=obj.phone,
            is_notifications_enabled=obj.is_notifications_enabled,
        )
        return object_
    
    @validator('join_time', pre=True)
    def join_time_validator(cls, v: datetime.datetime):
        return timezone.localtime(v)

class SupportRequest(BaseModel):
    id: int
    user_id: int
    created_time: datetime.datetime
    message_id_to_edit: int


class Operator(BaseModel):
    telegram_id: int
    full_name: str

class Town(BaseModel):
    id: int
    name: str

    @classmethod
    def parse_obj(cls: Type['Town'], obj: Any) -> 'Town':
        return cls(
            id=obj.id,
            name=obj.name,
        )

class Station(BaseModel):
    id: int
    name: str
    town: Town
    code: str
    laititude: float
    longitude: float
    departure_time: datetime.datetime | None

    @classmethod
    def parse_obj(cls: Type['Station'], obj: Any) -> 'Station':
        if obj is None:
            return None
        return cls(
            id=obj.id,
            name=obj.name,
            laititude=obj.laititude,
            longitude=obj.longitude,
            code=obj.code,
            town=Town.parse_obj(obj.town),
            departure_time=obj.departure_time if hasattr(obj, 'departure_time') else None,
        )
    
    @property
    def full_name(self) -> str:
        return f'{self.town.name}-{self.name}'

    @validator('departure_time', pre=True)
    def departure_time_validator(cls, v: datetime.datetime):
        try:
            return timezone.localtime(v)
        except AttributeError:
            return None


class Driver(BaseModel):
    telegram_id: int
    full_name: str
    phone: str
    
    @classmethod
    def parse_obj(cls: Type['Driver'], obj: Any) -> 'Driver':
        return cls(
            telegram_id=obj.telegram_id,
            full_name=obj.full_name,
            phone=obj.phone,
        )


class BusOption(BaseModel):
    id: int
    name: str
    
    @classmethod
    def parse_obj(cls: Type['BusOption'], obj: Any) -> 'BusOption':
        return cls(
            id=obj.id,
            name=obj.name,
        )


class Bus(BaseModel):
    id: int
    photos: list[str]
    seats: int
    name: str
    numbers: str
    description: str
    options: list[BusOption] | list
    code: str

    @classmethod
    def parse_obj(cls: Type['Bus'], obj: Any) -> 'Bus':
        return cls(
            id=obj.id,
            photos=[o.photo.path for o in obj.photos.all()],
            seats=obj.seats,
            name=obj.name,
            numbers=obj.numbers,
            description=obj.description,
            code=obj.code,
            options=[BusOption.parse_obj(o) for o in obj.options.all()],
        )

    

class Route(BaseModel):
    
    id: int 
    start_station: Station
    end_station: Station
    bus: Bus
    driver: Driver
    active: bool
    is_regular: bool
    code: str
    departure_time: datetime.datetime | None = None
    arrival_time: datetime.datetime | None = None
    package_price: int | None = None
    ticket_price: int | None = None
    available_seats: int | None = None
    user_start_station: Station | None = None
    user_end_station: Station | None = None
    user_departure_time: datetime.datetime | None = None
    user_arrival_time: datetime.datetime | None = None

    @classmethod
    def parse_obj(cls: Type['Route'], obj: Any, **kwargs) -> 'Route':
        return cls(
            id=obj.id,
            start_station=Station.parse_obj(obj.start_station),
            end_station=Station.parse_obj(obj.end_station),
            bus=Bus.parse_obj(obj.bus),
            driver=Driver.parse_obj(obj.driver),
            active=obj.active,
            code=obj.code,
            is_regular=obj.is_regular,
            departure_time=obj.departure_time if hasattr(obj, 'departure_time') else None,
            arrival_time=obj.arrival_time if hasattr(obj, 'arrival_time') else None,
            package_price=obj.package_price if hasattr(obj, 'package_price') else None,
            ticket_price=obj.ticket_price if hasattr(obj, 'ticket_price') else None,
            available_seats=obj.available_seats if hasattr(obj, 'available_seats') else None,
            user_start_station=Station.parse_obj(obj.user_start_station) if hasattr(obj, 'user_start_station') else None,
            user_end_station=Station.parse_obj(obj.user_end_station) if hasattr(obj, 'user_end_station') else None,
            user_departure_time=obj.user_departure_time if hasattr(obj, 'user_departure_time') else None,
            user_arrival_time=obj.user_arrival_time if hasattr(obj, 'user_arrival_time') else None,
        )
    
    @validator('*', pre=True)
    def validator(cls, v: datetime.datetime):
        if isinstance(v, datetime.datetime):
            return timezone.localtime(v)
        return v



class TicketType(BaseModel):
    id: int
    name: str
    discount: int

    @classmethod
    def parse_obj(cls: Type['TicketType'], obj: Any) -> 'TicketType':
        return cls(
            id=obj.id,
            name=obj.name,
            discount=obj.discount,
        )

class Person(BaseModel):
    id: int
    name: str
    surname: str
    phone: str | None = None

    @classmethod
    def parse_obj(cls: Type['Person'], obj: Any) -> 'Person':
        return cls(
            id=obj.id,
            name=obj.name,
            surname=obj.surname,
            phone=obj.phone,
        )


class Ticket(BaseModel):
    id: int
    owner: TelegramUser
    route: Route
    start_station: Station
    end_station: Station
    is_paid: bool
    type: TicketType
    ticket_code: uuid.UUID
    passenger: Person
    is_booked: bool
    payment_id: int | None = None
    paid_time: datetime.datetime | None = None
    departure_time: datetime.datetime | None = None
    arrival_time: datetime.datetime | None = None
    price: int | None = None

    @classmethod
    def parse_obj(cls: Type['Ticket'], obj: Any, **kwargs) -> 'Ticket':
        return cls(
            id=obj.id,
            owner=TelegramUser.parse_obj(obj.owner),
            route=Route.parse_obj(obj.route),
            start_station=Station.parse_obj(obj.start_station),
            end_station=Station.parse_obj(obj.end_station),
            is_paid=obj.is_paid,
            payment_id=obj.payment_id,
            ticket_code=obj.ticket_code,
            passenger=Person.parse_obj(obj.passenger),
            is_booked=obj.is_booked,
            type=TicketType.parse_obj(obj.type),
            paid_time=obj.paid_time.astimezone(timezone.get_current_timezone()) if obj.paid_time else None,
            departure_time=obj.departure_time if hasattr(obj, 'departure_time') else None,
            arrival_time=obj.arrival_time if hasattr(obj, 'arrival_time') else None,
            price=obj.price if hasattr(obj, 'price') else None,
            **kwargs
        )


    @validator('price', always=True)
    def validate_price(cls, value, values):
        if value is None:
            return value
        cls.discount = math.ceil((int(value)/100) *  values['type'].discount)
        price = int(value) - cls.discount
        return int(price)
    
    @validator('departure_time', 'arrival_time', 'paid_time', pre=True)
    def join_time_validator(cls, v: datetime.datetime):
        return timezone.localtime(v)


class Package(BaseModel):
    id: int
    owner: TelegramUser
    route: Route
    start_station: Station
    end_station: Station
    is_paid: bool
    departure_time: datetime.datetime | None = None
    arrival_time: datetime.datetime | None = None
    price: int | None = None
    paid_time: datetime.datetime | None = None
    package_code: str
    sender: Person
    receiver: Person
    payment_id: str | None

    @classmethod
    def parse_obj(cls: Type['Package'], obj: Any, **kwargs) -> 'Package':
        return cls(
            id=obj.id,
            owner=TelegramUser.parse_obj(obj.owner),
            route=Route.parse_obj(obj.route),
            start_station=Station.parse_obj(obj.start_station),
            end_station=Station.parse_obj(obj.end_station),
            is_paid=obj.is_paid,
            departure_time=obj.departure_time if hasattr(obj, 'departure_time') else None,
            arrival_time=obj.arrival_time if hasattr(obj, 'arrival_time') else None,
            sender=Person.parse_obj(obj.sender),
            receiver=Person.parse_obj(obj.receiver),
            package_code=obj.package_code,
            payment_id=obj.payment_id,
            price=obj.price if hasattr(obj, 'price') else None,
            paid_time=obj.paid_time.astimezone(timezone.get_current_timezone()) if obj.paid_time else None,
            **kwargs
        )

    @validator('departure_time', 'arrival_time', pre=True)
    def join_time_validator(cls, v: datetime.datetime):
        return timezone.localtime(v)



        
class ChosenRouteData(BaseModel):
    start_station: Station | None
    end_station: Station | None
    route: Route | None
    tickets_count: int | None
    persons: dict[int, Person] | None

    @classmethod
    def create_empty(cls: Type['ChosenRouteData']) -> 'ChosenRouteData':
        return cls(
            start_station=None,
            end_station=None,
            route=None,
            tickets_count=None,
            persons=None,
        )
    


    # departure_time: datetime.datetime | None
    # passenger_name: str | None
    # passenger_surname: str | None
    # package_price: int | None
    # ticket_price: int | None
    # ticket_type: TicketType | None
    # ticket: Ticket | None
    # invoice_message_id: str | None
    # sender_name: str | None
    # sender_phone: str | None
    # sender_surname: str | None
    # receiver_name: str | None
    # receiver_phone: str | None
    # receiver_surname: str | None

    

    # @classmethod
    # def parse_obj(
    #     cls: Type['ChosenRouteData'],
    #     obj: Any
    # ) -> 'ChosenRouteData':
    #     return cls(
    #         id=obj.id,
    #         user=TelegramUser.parse_obj(obj.user),
    #         start_message_id=obj.start_message_id,
    #         from_station=Station.parse_obj(obj.from_station),
    #         to_station=Station.parse_obj(obj.to_station),
    #         route=Route.parse_obj(obj.route) if obj.route else None,
    #         ticket_type=TicketType.parse_obj(obj.ticket_type) if obj.ticket_type else None,
    #         invoice_message_id=obj.invoice_message_id,
    #         passenger_name=obj.passenger_name,
    #         passenger_surname=obj.passenger_surname,
    #         sender_name=obj.sender_name,
    #         sender_surname=obj.sender_surname,
    #         sender_phone=obj.sender_phone,
    #         receiver_name=obj.receiver_name,
    #         receiver_phone=obj.receiver_phone,
    #         receiver_surname=obj.receiver_surname,
    #         departure_time=obj.departure_time if hasattr(obj, 'departure_time') else None,
    #         package_price=obj.package_price if hasattr(obj, 'package_price') else None,
    #         ticket_price=obj.ticket_price if hasattr(obj, 'ticket_price') else None,
    #         ticket=Ticket.parse_obj(obj.ticket) if obj.ticket else None,
    #     )
    
    # @validator('departure_time', pre=True)
    # def join_time_validator(cls, v: datetime.datetime):
        # return timezone.localtime(v)


class Payment(BaseModel):
    result: str
    payment_id: int
    action: str
    status: str
    version: int
    type: str
    paytype: str
    public_key: str
    acq_id: int
    order_id: str
    liqpay_order_id: str
    description: str
    sender_phone: str | None = None
    sender_card_mask2: str
    sender_card_bank: str
    sender_card_type: str
    sender_card_country: int
    amount: float
    currency: str
    sender_commission: float
    receiver_commission: float
    agent_commission: float
    amount_debit: float
    amount_credit: float
    commission_debit: float
    commission_credit: float
    currency_debit: str
    currency_credit: str
    sender_bonus: float
    amount_bonus: float
    mpi_eci: str
    is_3ds: bool
    create_date: int
    end_date: int
    transaction_id: int

