from django.contrib import admin
from django import forms

from web.app import models

# Register your models here.


# class PriceForm(forms.ModelForm):
    
#     field = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))

#     def save(self, commit=True):
#         field = self.cleaned_data['field']
#         super().save(commit=commit)

#     class Meta:
#         model = models.Price
#         fields = [field.name for field in models.Price._meta.get_fields() if field.name != 'id'] 

# setattr()


class RouteStationInline(admin.TabularInline):
    model = models.RouteStation
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

    def get_model_perms(self, request) -> dict[str, bool]:
        return {}

class StationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'town', 'is_popular')
    list_editable = ('is_popular', 'town', 'name')

class BusAdmin(admin.ModelAdmin):
    list_display = ('id', 'seats', )

    filter_horizontal = ('photos', )

class DriverAdmin(admin.ModelAdmin):
    list_display = ('full_name', )

    def get_model_perms(self, request) -> dict[str, bool]:
        return {}

class RouteAdmin(admin.ModelAdmin):
    list_display = ('id',  'bus', 'driver')

    inlines = [RouteStationInline, PriceInline]
    
    
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'route', 'is_paid', 'start_station', 'end_station')

    
class DissalovedStationAdmin(admin.ModelAdmin):
    list_display = ('id', 'from_station', 'to_station')

class PriceAdmin(admin.ModelAdmin):
    list_display = ('id', 'from_station', 'to_station', 'ticket_price', 'package_price')
   
    def get_model_perms(self, request) -> dict[str, bool]:
        return {}

class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'discount')

    def get_model_perms(self, request) -> dict[str, bool]:
        return {}

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
admin.site.register(models.DisallowedWay, DissalovedStationAdmin)
admin.site.register(models.Price, PriceAdmin)
admin.site.register(models.TicketType, TicketTypeAdmin)