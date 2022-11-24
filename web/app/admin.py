from django.contrib import admin

from web.app import models
from web.translations import models as translation_models


class StationTranslationInline(admin.TabularInline):
    model = translation_models.StationTranslations
    extra = 0

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

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj):
        fields =  super().get_readonly_fields(request, obj)
        fields = ['from_station', 'to_station']
        return fields

class TownAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name', )

    inlines = [TownTranslationInline]




class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'discount')
    search_fields = ('name', )


class StationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'town', 'is_popular')
    list_editable = ('is_popular', )

    list_filter = ('town', )
    search_fields = ('name', )

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
        'id',  'bus', 'driver', 'departure_time', 'active', 'start_station', 'end_station'
    )
    fields = (
        ('start_station', 'end_station'),
        ('bus', 'driver'),
        'active',
        'is_regular',
    )
    search_fields = ('departure_time', )
    list_filter = ('active', 'start_station', 'end_station')

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