from django.db import models

from ..app.models import Bus, BusOption, Language, Station, TicketType, Town

class TicketTypeTranslations(models.Model):
    class Meta:
        verbose_name = 'Ticket Type Translation'
        verbose_name_plural = 'Ticket Type Translations'
        db_table = 'ticket_type_translations'

    id = models.AutoField(primary_key=True)
    ticket_type = models.ForeignKey(
        to=TicketType,
        on_delete=models.CASCADE,
    )
    language = models.ForeignKey(
        to=Language,
        on_delete=models.CASCADE,
    )
    translation = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f'{self.ticket_type} ({self.language})'

class BusTranslation(models.Model):
    class Meta:
        verbose_name = 'Bus Translation'
        verbose_name_plural = 'Bus Translations'
        db_table = 'bus_translations'

    id = models.AutoField(primary_key=True)
    bus = models.ForeignKey(
        to=Bus,
        on_delete=models.CASCADE,
    )
    language = models.ForeignKey(
        to=Language,
        on_delete=models.CASCADE,
    )
    description_translation = models.TextField()
    name_translation = models.CharField(max_length=255)


class BusOptionTranslation(models.Model):
    class Meta:
        verbose_name = 'Bus Option Translation'
        verbose_name_plural = 'Bus Option Translations'
        db_table = 'bus_option_translations'

    id = models.AutoField(primary_key=True)
    bus_option = models.ForeignKey(
        to=BusOption,
        on_delete=models.CASCADE,
    )
    language = models.ForeignKey(
        to=Language,
        on_delete=models.CASCADE,
    )
    translation = models.CharField(max_length=255)
 
class StationTranslations(models.Model):
    class Meta:
        verbose_name = 'Station Translation'
        verbose_name_plural = 'Station Translations'
        db_table = 'stations_translations'
    
    id = models.AutoField(primary_key=True)
    station = models.ForeignKey(
        to=Station,
        on_delete=models.CASCADE,
    )
    language = models.ForeignKey(
        to=Language,
        on_delete=models.CASCADE,
    )
    translation = models.CharField(max_length=255)

    def __str__(self):
        return (
            f'{self.station} ({self.language})'
        )


class TownTranslations(models.Model):
    class Meta:
        verbose_name = 'Town Translation'
        verbose_name_plural = 'Town Translations'
        db_table = 'towns_translations'
    
    id = models.AutoField(primary_key=True)
    town = models.ForeignKey(
        to=Town,
        on_delete=models.CASCADE,
    )
    language = models.ForeignKey(
        to=Language,
        on_delete=models.CASCADE,
    )
    translation = models.CharField(max_length=255)

    def __str__(self):
        return (
            f'{self.town} ({self.language})'
        )
 