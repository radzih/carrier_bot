from django.contrib import admin

from web.app import models
# Register your models here.

class TownAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

class StationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'town', 'is_popular')
    list_editable = ('is_popular', 'town')

class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'join_time', )

class SupportRequestAdmin(admin.ModelAdmin):
    list_display = list(
        field.name for field in models.SupportRequest._meta.get_fields())

class UesrTicketChooseDataAdmin(admin.ModelAdmin):
    list_display = ('user', 'start_message_id', 'from_station', 'to_station')

class BusAdmin(admin.ModelAdmin):
    list_display = ('id', 'seats', )

class DriverAdmin(admin.ModelAdmin):
    list_display = ('full_name', )

class RouteAdmin(admin.ModelAdmin):
    list_display = ('id',  'bus', 'driver')

class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'route', 'is_paid', 'start_station', 'end_station')

class RouteStationsAdmin(admin.ModelAdmin):
    list_display = ('id', 'station')

class DissalovedStationAdmin(admin.ModelAdmin):
    list_display = ('id', 'from_station', 'to_station')

class PriceAdmin(admin.ModelAdmin):
    list_display = ('id', 'from_station', 'to_station', 'ticket_price', 'package_price')

class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'discount')

class TownLanguageAdmin(admin.ModelAdmin):
    list_display = ('id', 'town', 'language')

class StationLanguageAdmin(admin.ModelAdmin):
    list_display = ('id', 'station', 'language')

class LanguageAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

class TicketTypeTranslationAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket_type', 'language')

class BusOptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

class BusOptionTranslationAdmin(admin.ModelAdmin):
    list_display = ('id', 'bus_option', 'language')

class BusTranslationAdmin(admin.ModelAdmin):
    list_display = ('id', 'bus', 'language')

class BusPhotosAdmin(admin.ModelAdmin):
    list_display = ('id',)


admin.site.register(models.BusPhotos, BusPhotosAdmin)    
admin.site.register(models.BusOption, BusOptionAdmin)
admin.site.register(models.BusOptionTranslation, BusOptionTranslationAdmin)
admin.site.register(models.BusTranslation, BusTranslationAdmin)
admin.site.register(models.TicketTypeTranslations, TicketTypeTranslationAdmin)
admin.site.register(models.Language, LanguageAdmin)
admin.site.register(models.TownTranslations, TownLanguageAdmin)
admin.site.register(models.StationTranslations, StationLanguageAdmin)
admin.site.register(models.Town, TownAdmin)
admin.site.register(models.Station, StationAdmin)
admin.site.register(models.TelegramUser, TelegramUserAdmin)
admin.site.register(models.SupportRequest, SupportRequestAdmin)
admin.site.register(models.Bus, BusAdmin)
admin.site.register(models.Driver, DriverAdmin)
admin.site.register(models.Route, RouteAdmin)
admin.site.register(models.Ticket, TicketAdmin)
admin.site.register(models.RouteStation, RouteStationsAdmin)
admin.site.register(models.DisallowedWay, DissalovedStationAdmin)
admin.site.register(models.Price, PriceAdmin)
admin.site.register(models.TicketType, TicketTypeAdmin)