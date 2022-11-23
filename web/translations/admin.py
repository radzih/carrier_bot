from django.contrib import admin
from . import models


class BusOptionTranslationAdmin(admin.ModelAdmin):
    list_display = ('id', 'bus_option', 'language')

class BusTranslationAdmin(admin.ModelAdmin):
    list_display = ('id', 'bus', 'language')

class StationLanguageAdmin(admin.ModelAdmin):
    list_display = ('id', 'station', 'language')

class TownLanguageAdmin(admin.ModelAdmin):
    list_display = ('id', 'town', 'language', 'translation')

    list_editable = ('translation', )

class TicketTypeTranslationAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket_type', 'language')


admin.site.register(models.BusOptionTranslation, BusOptionTranslationAdmin)
admin.site.register(models.TicketTypeTranslations, TicketTypeTranslationAdmin)
admin.site.register(models.TownTranslations, TownLanguageAdmin)
admin.site.register(models.StationTranslations, StationLanguageAdmin)
admin.site.register(models.BusTranslation, BusTranslationAdmin)
