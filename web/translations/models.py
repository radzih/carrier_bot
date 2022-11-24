from django.db import models

from ..app.models import Bus, BusOption, Language, Station, TicketType, Town

class TicketTypeTranslations(models.Model):
    class Meta:
        verbose_name = 'Переклад типу квитка'
        verbose_name_plural = 'Переклади типів квитків'
        db_table = 'ticket_type_translations'

    id = models.AutoField(primary_key=True)
    ticket_type = models.ForeignKey(
        to=TicketType,
        on_delete=models.CASCADE,
    )
    language = models.ForeignKey(
        to=Language,
        on_delete=models.CASCADE,
        verbose_name='Мова',
    )
    translation = models.CharField(max_length=255, verbose_name='Переклад')

    def __str__(self) -> str:
        return f'{self.ticket_type} ({self.language})'

class BusTranslation(models.Model):
    class Meta:
        verbose_name = 'Переклад автобуса'
        verbose_name_plural = 'Переклади автобусів'
        db_table = 'bus_translations'

    id = models.AutoField(primary_key=True)
    bus = models.ForeignKey(
        to=Bus,
        on_delete=models.CASCADE,
    )
    language = models.ForeignKey(
        to=Language,
        on_delete=models.CASCADE,
        verbose_name='Мова',
    )
    description_translation = models.TextField(verbose_name='Переклад опису')
    name_translation = models.CharField(max_length=255, verbose_name='Переклад назви')


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
        verbose_name = 'Переклад станції'
        verbose_name_plural = 'Переклади станцій'
        db_table = 'stations_translations'
    
    id = models.AutoField(primary_key=True)
    station = models.ForeignKey(
        to=Station,
        on_delete=models.CASCADE,
    )
    language = models.ForeignKey(
        to=Language,
        on_delete=models.CASCADE,
        verbose_name='Мова',
    )
    translation = models.CharField(max_length=255, verbose_name='Переклад')

    def __str__(self):
        return (
            f'{self.station} ({self.language})'
        )


class TownTranslations(models.Model):
    class Meta:
        verbose_name = 'Переклад міста'
        verbose_name_plural = 'Переклади міст'
        db_table = 'towns_translations'
    
    id = models.AutoField(primary_key=True)
    town = models.ForeignKey(
        to=Town,
        on_delete=models.CASCADE,
    )
    language = models.ForeignKey(
        to=Language,
        on_delete=models.CASCADE,
        verbose_name='Мова',
    )
    translation = models.CharField(max_length=255, verbose_name='Переклад')

    def __str__(self):
        return (
            f'{self.town} ({self.language})'
        )
 