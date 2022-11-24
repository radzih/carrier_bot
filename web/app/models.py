import logging
import math
import datetime
import uuid
from uuid import uuid4

from django.db import models
from django.utils import timezone
from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError



def four_number_code_generator():
    return uuid.uuid4().hex[:4]

def six_number_code_generator():
    return uuid.uuid4().hex[:6]


class Language(models.Model):

    class Meta:
        verbose_name = 'Мова'
        verbose_name_plural = 'Мови'
        db_table = 'language'
    
    name = models.CharField(max_length=20)    
    code = models.CharField(max_length=2)

    def __str__(self):
        return self.name


class TelegramUser(models.Model):
    class Meta:
        verbose_name = 'Telegram User'
        verbose_name_plural = 'Telegram Users'
        db_table = 'telegram_user'

    id = models.AutoField(primary_key=True)
    telegram_id = models.BigIntegerField(null=True, unique=True, blank=True)
    full_name = models.CharField(max_length=255)
    join_time = models.DateTimeField(auto_now_add=True)
    phone = models.CharField(max_length=15)
    language = models.ForeignKey(Language, on_delete=models.CASCADE, default=1)
    is_notifications_enabled = models.BooleanField(default=True)
    
    def __str__(self):
        return f'{self.full_name} ({self.telegram_id})'

        
class SupportRequest(models.Model):
    class Meta:
        verbose_name = 'Support Request'
        verbose_name_plural = 'Support Requests'
        db_table = 'support_request'
    
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    created_time = models.DateTimeField(auto_now_add=True)
    message_id_to_edit = models.IntegerField()
    
    def __str__(self):
        return f'{self.user} at {self.created_time}'
    
    def dict(self):
        return {
            'id': self.id,
            'user_id': self.user.telegram_id,
            'created_time': self.created_time,
            'message_id_to_edit': self.message_id_to_edit,
        }


class SendingMessage(models.Model):
    class Meta:
        verbose_name = 'Sending Message'
        verbose_name_plural = 'Sending Messages'
        db_table = 'sending_message'
    
    id = models.AutoField(primary_key=True)
    text = models.TextField()


class Operator(models.Model):
    class Meta:
        verbose_name = 'Operator'
        verbose_name_plural = 'Operators'
        db_table = 'operator'
    
    telegram_id = models.BigIntegerField(unique=True, primary_key=True)
    full_name = models.CharField(max_length=255)
    
    def __str__(self):
        return f'{self.full_name} ({self.telegram_id})'

    def dict(self):
        return {
            'telegram_id': self.telegram_id,
            'full_name': self.full_name,
        }
    

class OperatorConfirmUUID(models.Model):
    class Meta:
        verbose_name = 'Operator Confirm Code'
        verbose_name_plural = 'Operator Confirm Codes'
        db_table = 'operator_confirm_code'
    
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    
    def __str__(self):
        return f'{self.uuid}'

    def dict(self):
        return {
            'uuid': self.uuid,
        }


class Town(models.Model):
    class Meta:
        verbose_name = 'Місто'
        verbose_name_plural = 'Міста'
        db_table = 'town'
    
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, verbose_name='Назва')
    
    def __str__(self):
        return f'{self.name}'

def sixiteens_hex_code_generator():
    return uuid.uuid4().hex[:16]

class Station(models.Model):
    class Meta:
        verbose_name = 'Станція'
        verbose_name_plural = 'Станції'
        db_table = 'station'
    
    id = models.AutoField(primary_key=True) 
    code = models.CharField(
        max_length=4, 
        unique=True,
        default=four_number_code_generator,
        editable=False
    )
    name = models.CharField(max_length=255, verbose_name='Назва')
    town = models.ForeignKey(Town, on_delete=models.CASCADE, verbose_name='Місто')
    latitude = models.FloatField(verbose_name='Широта')
    longitude = models.FloatField(verbose_name='Довгота')
    is_popular = models.BooleanField(default=False, verbose_name='Популярна')

    def __str__(self):
        return f'{self.town.name}-{self.name}'


class BusPhotos(models.Model):
    class Meta:
        verbose_name = 'Bus Photo'
        verbose_name_plural = 'Bus Photos'
        db_table = 'buses_photos'

    photo = models.ImageField(upload_to='data/buses')

class Bus(models.Model):
    class Meta:
        verbose_name = 'Автобус'
        verbose_name_plural = 'Автобуси'
        db_table = 'bus'

    id = models.AutoField(primary_key=True)
    seats = models.IntegerField(verbose_name='Кількість місць')
    name = models.CharField(max_length=255, verbose_name='Назва')
    numbers = models.CharField(max_length=8, verbose_name='Номери')
    description = models.TextField(verbose_name='Опис')
    options = models.ManyToManyField('BusOption', blank=True, verbose_name='Опції')
    photos = models.ManyToManyField(
        BusPhotos,
        related_name='photos',
        verbose_name='Фото'
    )
    code = models.CharField(
        max_length=16, 
        unique=True,
        default=sixiteens_hex_code_generator,
        editable=False
    )
    
    def __str__(self):
        return f'{self.name}({self.seats} місць)'


class Driver(models.Model):
    class Meta:
        verbose_name = 'Водій'
        verbose_name_plural = 'Водії'
        db_table = 'driver'

    telegram_id = models.BigIntegerField(unique=True, primary_key=True)
    full_name = models.CharField(max_length=255, verbose_name='ПІБ')
    phone = models.CharField(max_length=15, verbose_name='Телефон')

    def __str__(self):
        return f'{self.full_name}'


class Route(models.Model):
    class Meta:
        db_table = 'route'
        verbose_name = 'Маршрут'
        verbose_name_plural = 'Маршрути'

    id = models.AutoField(primary_key=True)
    start_station = models.ForeignKey(
        to=Station,
        on_delete=models.CASCADE,
        related_name='route_start_station',
        verbose_name='Початкова станція',
    )
    end_station = models.ForeignKey(
        to=Station,
        on_delete=models.CASCADE,
        related_name='route_end_station',
        verbose_name='Кінцева станція',
    )
    code = models.CharField(
        max_length=6, 
        unique=True,
        default=six_number_code_generator,
        editable=False
    )
    active = models.BooleanField(default=True, verbose_name='Активний')
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, verbose_name='Автобус')
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, verbose_name='Водій')
    is_regular = models.BooleanField(default=False, verbose_name='Регулярний')


    def __str__(self):
        departure_time = self.departure_time() 
        return f'{self.start_station}-{self.end_station}({departure_time})'

    def departure_time(self):
        first_station = RouteStation.objects.filter(
            route=self
        ).order_by('station_index').first()
        departure_time = '00'
        if first_station:
            departure_time = first_station.departure_time.strftime('%d.%m')
        return departure_time
    departure_time.short_description = 'Час відправлення'
 
    @property
    def package_price(self):
        return Price.objects.filter(route=self).first().package_price


class TicketType(models.Model):
    class Meta:
        db_table = 'ticket_type'
        verbose_name = 'Типи квитків'
        verbose_name_plural = 'Типи квитків'

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, verbose_name='Назва')
    discount = models.IntegerField(verbose_name='Знижка в відсотках')

    def __str__(self):
        return f'{self.name}'


class Ticket(models.Model):
    class Meta:
        db_table = 'ticket'
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'

    id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(
        to=TelegramUser,
        on_delete=models.CASCADE
    )
    route = models.ForeignKey(
        to=Route,
        on_delete=models.CASCADE
    )
    start_station = models.ForeignKey(
        to=Station,
        on_delete=models.CASCADE,
        related_name='ticket_start_station'
    )
    end_station = models.ForeignKey(
        to=Station,
        on_delete=models.CASCADE,
        related_name='ticket_end_station'
    )
    type = models.ForeignKey(
        to=TicketType,
        on_delete=models.CASCADE,
        related_name='ticket_type',
    )
    passenger = models.ForeignKey(
        to='Person',
        on_delete=models.CASCADE,
    )
    ticket_code = models.UUIDField(default=uuid.uuid4(), editable=False)
    is_paid = models.BooleanField()
    is_booked = models.BooleanField()
    payment_id = models.IntegerField(null=True)
    paid_time = models.DateTimeField(null=True)
    created_time = models.DateTimeField(auto_now_add=True)


    @sync_to_async
    def delete_after_10min(self):
        if not self.is_booked:
            return
        if self.created_time + datetime.timedelta(minutes=10) < timezone.now():
            self.delete()


class Package(models.Model):
    class Meta:
        db_table = 'package'
        verbose_name = 'Package'
        verbose_name_plural = 'Packages'

    id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(
        to=TelegramUser,
        on_delete=models.CASCADE
    )
    route = models.ForeignKey(
        to=Route,
        on_delete=models.CASCADE
    )
    start_station = models.ForeignKey(
        to=Station,
        on_delete=models.CASCADE,
        related_name='package_start_station'
    )
    end_station = models.ForeignKey(
        to=Station,
        on_delete=models.CASCADE,
        related_name='package_end_station'
    )
    is_paid = models.BooleanField()
    sender = models.ForeignKey(
        to='Person',
        on_delete=models.CASCADE,
        related_name='package_sender'
    )
    receiver = models.ForeignKey(
        to='Person',
        on_delete=models.CASCADE,
        related_name='package_receiver'
    )
    package_code = models.CharField(default=str(uuid.uuid4())[:12], editable=False, max_length=12)
    payment_id  = models.CharField(null=True, max_length=255)
    paid_time = models.DateTimeField()


class Price(models.Model):
    class Meta:
        db_table = 'ticket_price'
        verbose_name = 'Ціни'
        verbose_name_plural = 'Ціни'

    id = models.AutoField(primary_key=True)
    route = models.ForeignKey(
        to=Route,
        on_delete=models.CASCADE,
        verbose_name='Маршрут'
    )
    from_station = models.ForeignKey(
        to=Station,
        on_delete=models.CASCADE,
        related_name='ticket_price_from_station',
        verbose_name='З станції',
    )
    to_station = models.ForeignKey(
        to=Station,
        on_delete=models.CASCADE,
        related_name='ticket_price_to_station',
        verbose_name='До станції',
    )
    ticket_price = models.DecimalField(
        decimal_places=2,
        max_digits=6,
        verbose_name='Ціна квитка',
    )
    package_price = models.DecimalField(
        decimal_places=2,
        max_digits=6,
        verbose_name='Ціна посилки',
    )

    def __str__(self):
        return f'{self.from_station} -> {self.to_station}'
    

class DisallowedWay(models.Model):
    class Meta:
        db_table = 'disallowed_way'
        verbose_name = 'Недопустимий маршрут'
        verbose_name_plural = 'Недопустимі маршрути'

    id = models.AutoField(primary_key=True)
    route = models.ForeignKey(
        to=Route,
        on_delete=models.CASCADE,
        verbose_name='Маршрут'
    )
    from_station = models.ForeignKey(
        to=Station,
        on_delete=models.CASCADE,
        related_name='disallowed_way_from_station',
        verbose_name='З станції',
    )
    to_station = models.ForeignKey(
        to=Station,
        on_delete=models.CASCADE,
        related_name='disallowed_way_to_station',
        verbose_name='До станції',
    )

    def __str__(self):
        return f'{self.from_station} -> {self.to_station}'


class RouteStation(models.Model):
    class Meta:
        verbose_name = 'Route Station'
        verbose_name_plural = 'Route Stations'
        db_table = 'routes_stations'
    
    id = models.AutoField(primary_key=True)
    station_index = models.IntegerField(verbose_name='Номер станції')
    station = models.ForeignKey(
        to=Station,
        on_delete=models.CASCADE,
        verbose_name='Станція'
    )
    route = models.ForeignKey(
        to=Route,
        on_delete=models.CASCADE,
        verbose_name='Маршрут'
    )
    departure_time = models.DateTimeField(verbose_name='Час відправлення')

    def __str__(self):
        return (
            f'{self.route} ({self.station_index})'
        )
    

class UserStartStationHistory(models.Model):
    class Meta:
        verbose_name = 'User Start Station History'
        verbose_name_plural = 'User Start Station History'
        db_table = 'user_start_station_history'

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    station = models.ForeignKey(Station, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user} ({self.station})'


class UserEndStationHistory(models.Model):
    class Meta:
        verbose_name = 'User End Station History'
        verbose_name_plural = 'User End Station History'
        db_table = 'user_end_station_history'

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    station = models.ForeignKey(Station, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user} ({self.station})'


class Person(models.Model):
    class Meta:
        verbose_name = 'Person'
        verbose_name_plural = 'Persons'
        db_table = 'persons'

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    surname = models.CharField(max_length=255)
    phone = models.CharField(max_length=255, null=True, blank=True)
    telegram_user = models.ForeignKey(
        to=TelegramUser,
        on_delete=models.CASCADE,
        related_name='telegram_user',
    )

    def __str__(self):
        return f'{self.name} {self.surname}'


    

class BusOption(models.Model):
    class Meta:
        verbose_name = 'Bus Option'
        verbose_name_plural = 'Bus Options'
        db_table = 'app_bus_options'

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, verbose_name='Назва')

    def __str__(self) -> str:
        return f'{self.name}'

       