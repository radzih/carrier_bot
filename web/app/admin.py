import datetime

from django.contrib import admin
from django.db.models import (
    OuterRef, Exists, Subquery, Q, Count, Sum, DecimalField, F,
    FloatField, Value, CharField, Func, IntegerField
)
from django.db.models.functions import Cast, Concat, Coalesce

from django.utils import timezone
from django.utils.translation import gettext_lazy

from web.app import models, actions
from web.translations import models as translation_models


admin.site.site_header = "Start Trans"
admin.site.site_url = None


class StationTranslationInline(admin.TabularInline):
    model = translation_models.StationTranslations
    extra = 0

    autocomplete_fields = ('station', )


class TownTranslationInline(admin.TabularInline):
    model = translation_models.TownTranslations
    extra = 0


class TicketTypeTranslationInline(admin.TabularInline):
    model = translation_models.TicketTypeTranslations
    extra = 0


class RouteStationInline(admin.TabularInline):
    model = models.RouteStation
    extra = 0


class DissallowedWayInline(admin.TabularInline):
    model = models.DisallowedWay
    extra = 0


class BusTranslationInline(admin.TabularInline):
    model = translation_models.BusTranslation
    extra = 0


class PriceInline(admin.TabularInline):
    model = models.Price
    extra: int = 0

    def has_add_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj):
        fields =  super().get_readonly_fields(request, obj)
        fields = ['from_station', 'to_station']
        return fields

        
class TicketInline(admin.TabularInline):
    model = models.Ticket
    extra = 0
    fields = (
        'route',
        ('start_station', 'end_station'),
        'type',
        'is_paid',
        'payment_id',
        'created_time',
        'passenger',
    )
    readonly_fields = (
        'route',
        'start_station',
        'end_station',
        'type',
        'is_paid',
        'payment_id',
        'created_time',
        'passenger',
    )

    def has_add_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj) -> bool:
        return False


class PackageInline(admin.TabularInline):
    model = models.Package
    extra = 0
    fields = (
        'route',
        ('start_station', 'end_station'),
        'is_paid',
        'payment_id',
        'sender',
        'receiver',
        'created_time',
    )
    readonly_fields = (
        'route',
        'start_station',
        'end_station',
        'is_paid',
        'payment_id',
        'sender',
        'receiver',
        'created_time',
    )

    def has_add_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj) -> bool:
        return False


class TownAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name', )

    inlines = [TownTranslationInline]


class RoutesInWeek(admin.SimpleListFilter):
    '''Show routes in week'''
    title = 'За датою відправлення'
    parameter_name = 'departure_time'

    def lookups(self, request, model_admin):
        return [
            ('Протягом наступних 7 днів', 'Протягом наступних 7 днів'),
            ('Протягом наступного місяця', 'Протягом наступного місяця'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'Протягом наступних 7 днів':
            return (
                queryset
                .annotate(
                    depart_time=Subquery(
                        models.RouteStation.objects
                        .filter(route=OuterRef('pk'))
                        .order_by('departure_time')
                        .values('departure_time')[:1]
                    )
                )
                .filter(
                    depart_time__gte=timezone.now(),
                    depart_time__lte=timezone.now() + datetime.timedelta(weeks=1),
                )
            )
        elif self.value() == 'Протягом наступного місяця':
            return (
                queryset
                .annotate(
                    depart_time=Subquery(
                        models.RouteStation.objects
                        .filter(route=OuterRef('pk'))
                        .order_by('departure_time')
                        .values('departure_time')[:1]
                    )
                )
                .filter(
                    depart_time__gte=timezone.now(),
                    depart_time__lte=timezone.now() + datetime.timedelta(weeks=4),
                )
            )


class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'discount')
    search_fields = ('name', )


class StationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'town', 'is_popular')
    list_editable = ('is_popular', )

    list_filter = ('town', )
    search_fields = ('name', )

    autocomplete_fields= ('town', )

    inlines = [StationTranslationInline]


class BusAdmin(admin.ModelAdmin):
    list_display = ('id', 'seats', 'name', 'numbers')
    filter_horizontal = ('photos', )

    fields = ('name', 'numbers', 'seats', 'photos')

    inlines = [BusTranslationInline]


class DriverAdmin(admin.ModelAdmin):
    list_display = ('full_name', )

    def get_model_perms(self, request) -> dict[str, bool]:
        return {}


class RouteAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'departure_time_admin', 'active', 'start_station', 'end_station'
    )
    fields = (
        ('start_station', 'end_station'),
        ('bus', 'driver'),
        'active',
        'is_regular',
    )
    # search_fields = ('departure_time', )
    list_filter = ('active', 'start_station', 'end_station', RoutesInWeek)

    actions = (actions.duplicate_route, actions.deactivate, actions.activate)

    inlines = [RouteStationInline, DissallowedWayInline, PriceInline]

    
class PriceAdmin(admin.ModelAdmin):
    list_display = ('id', 'from_station', 'to_station', 'ticket_price', 'package_price')
   
    def get_model_perms(self, request) -> dict[str, bool]:
        return {}


class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'discount')

    inlines = [TicketTypeTranslationInline]


class BusOptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

    def get_model_perms(self, request) -> dict[str, bool]:
        return {}


class BusPhotosAdmin(admin.ModelAdmin):
    list_display = ('id',)

    def get_model_perms(self, request) -> dict[str, bool]:
        return {}


class RouteStationsAdmin(admin.ModelAdmin):
    list_display = ('id', 'route', 'station')

    def get_model_perms(self, request) -> dict[str, bool]:
        return {}


class UserAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'join_time')
    fields = ('full_name', 'phone', 'join_time')
    readonly_fields = ('join_time', 'phone', 'full_name')

    search_fields = ('full_name', 'phone')

    inlines = [TicketInline, PackageInline]

    def has_add_permission(self, request):
        return False


class TicketAdmin(admin.ModelAdmin):
    list_display = (
        'start_station',
        'end_station',
        'type',
        'is_paid',
        'created_time',
        'owner'
    )
    search_fields = ('start_station__name', 'end_station__name')
    fields = (
        'route',
        ('start_station', 'end_station'),
        'type',
        'is_paid',
        'payment_id',
        'created_time',
        'passenger',
        'owner'
    )
    readonly_fields = (
        'route',
        'start_station',
        'end_station',
        'type',
        'is_paid',
        'payment_id',
        'created_time',
        'passenger',
        'owner'
    )
    list_filter = ('route', 'created_time', 'is_paid')


class StatisticsAdmin(admin.ModelAdmin):
    change_list_template = 'admin_panel/change_list.html'


    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(
            request,
            extra_context=extra_context,
        )

        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response

        metrics = {
            'total': Subquery(
                models.Ticket.objects.filter(
                    route=OuterRef('pk')
                )
                .values('route')
                .annotate(count=Coalesce(Count('id'), Value(0),
                                         output_field=IntegerField()))
                .values('count'),
            ),
            'total_paid': Subquery(
                models.Ticket.objects.filter(
                    route=OuterRef('pk'),
                    is_paid=True,
                )
                .values('route')
                .annotate(count=Coalesce(Count('id'), Value(0),
                                         output_field=IntegerField()))
                .values('count'),
            ),
            'total_unpaid': Subquery(
                models.Ticket.objects.filter(
                    route=OuterRef('pk'),
                    is_paid=False
                )
                .values('route')
                .annotate(count=Coalesce(Count('id'), Value(0),
                                         output_field=IntegerField()))
                .values('count'),
            ),
            'total_sales': Subquery(
                models.Ticket.objects.filter(
                    route=OuterRef('pk')
                )
                .annotate(
                    price=Subquery(
                        models.Price.objects.filter(
                            route=OuterRef('route'),
                            from_station=OuterRef('start_station'),
                            to_station=OuterRef('end_station')
                        )[:1]
                        .values(
                            price=Cast(
                                F("ticket_price")-
                                F('ticket_price')/100*
                                OuterRef('type__discount'),
                                output_field=FloatField()
                            )
                        )
                    )
                )
                .values('price')
                .annotate(price_sum=Sum("price"))
                .values('price')[:1]
                
            )
        }

        response.context_data['summary'] = list(
            qs
            .annotate(
                name=Concat(
                    F("start_station__town__name"),
                    Value('-'),
                    F("start_station__name"),
                    Value(' - '),
                    F("end_station__town__name"),
                    Value('-'),
                    F("end_station__name"),
                    Subquery(
                        models.RouteStation.objects.filter(
                            route=OuterRef("pk"),
                            station_index=1
                        )
                        .annotate(
                            formated_time=Func(
                                F('departure_time'),
                                Value('(DD.MM)'),
                                function='to_char',
                                output_field=CharField()
                            ) 
                        )
                        .values('formated_time')
                    ),
                    output_field=CharField()
                )
            )
            .values('name')
            .annotate(**metrics)
            .filter(total__gt=0)
            # .order_by('-total_sales')
        )

        return response

    def has_add_permission(self, request) -> bool:
        return False

class StatisticsWeekAdmin(admin.ModelAdmin):
    change_list_template = 'admin_panel/change_list.html'


    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(
            request,
            extra_context=extra_context,
        )

        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response

        metrics = {
            'total': Subquery(
                models.Ticket.objects.filter(
                    route=OuterRef('pk')
                )
                .values('route')
                .annotate(count=Coalesce(Count('id'), Value(0),
                                         output_field=IntegerField()))
                .values('count'),
            ),
            'total_paid': Subquery(
                models.Ticket.objects.filter(
                    route=OuterRef('pk'),
                    is_paid=True,
                )
                .values('route')
                .annotate(count=Coalesce(Count('id'), Value(0),
                                         output_field=IntegerField()))
                .values('count'),
            ),
            'total_unpaid': Subquery(
                models.Ticket.objects.filter(
                    route=OuterRef('pk'),
                    is_paid=False
                )
                .values('route')
                .annotate(count=Coalesce(Count('id'), Value(0),
                                         output_field=IntegerField()))
                .values('count'),
            ),
            'total_sales': Subquery(
                models.Ticket.objects.filter(
                    route=OuterRef('pk')
                )
                .annotate(
                    price=Subquery(
                        models.Price.objects.filter(
                            route=OuterRef('route'),
                            from_station=OuterRef('start_station'),
                            to_station=OuterRef('end_station')
                        )[:1]
                        .values(
                            price=Cast(
                                F("ticket_price")-
                                F('ticket_price')/100*
                                OuterRef('type__discount'),
                                output_field=FloatField()
                            )
                        )
                    )
                )
                .values('price')
                .annotate(price_sum=Sum("price"))
                .values('price')[:1]
                
            )
        }

        response.context_data['summary'] = list(
            qs
            .annotate(
                name=Concat(
                    F("start_station__town__name"),
                    Value('-'),
                    F("start_station__name"),
                    Value(' - '),
                    F("end_station__town__name"),
                    Value('-'),
                    F("end_station__name"),
                    Subquery(
                        models.RouteStation.objects.filter(
                            route=OuterRef("pk"),
                            station_index=1
                        )
                        .annotate(
                            formated_time=Func(
                                F('departure_time'),
                                Value('(DD.MM)'),
                                function='to_char',
                                output_field=CharField()
                            ) 
                        )
                        .values('formated_time')
                    ),
                    output_field=CharField()
                )
            )
            .annotate(
                departure_time= Subquery(
                    models.RouteStation.objects.filter(
                        route=OuterRef("pk"),
                        station_index=1
                    )
                    .values('departure_time')
                ),
            )
            .filter(departure_time__lt=timezone.now()+datetime.timedelta(days=3))
            .filter(departure_time__gt=timezone.now()-datetime.timedelta(days=3))
            .values('name')
            .annotate(**metrics)
            .filter(total__gt=0)
            # .order_by('-total_sales')
        )

        return response

    def has_add_permission(self, request) -> bool:
        return False

admin.site.register(models.StatisticsWeek, StatisticsWeekAdmin)   
admin.site.register(models.Statistics, StatisticsAdmin)
admin.site.register(models.Ticket, TicketAdmin)
admin.site.register(models.TelegramUser, UserAdmin)
admin.site.register(models.BusPhotos, BusPhotosAdmin)    
admin.site.register(models.BusOption, BusOptionAdmin)
admin.site.register(models.Town, TownAdmin)
admin.site.register(models.Station, StationAdmin)
admin.site.register(models.Bus, BusAdmin)
admin.site.register(models.Driver, DriverAdmin)
admin.site.register(models.Route, RouteAdmin)
admin.site.register(models.RouteStation, RouteStationsAdmin)
admin.site.register(models.Price, PriceAdmin)
admin.site.register(models.TicketType, TicketTypeAdmin)
admin.site.register(models.QuickAnswers)