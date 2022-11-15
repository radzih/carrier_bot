from aiogram.dispatcher import Dispatcher, FSMContext

from .end_station import register_end_staion_handlers
from .start_station import register_start_station_handlers
from .finded_station import register_finded_station_handlers
from .route_date import register_route_date_handlers
from .show_routes import register_show_routes_handlers
from .see_route import register_see_route_handlers
from .get_passengers import register_get_passengers_handlers
from .pay import register_pay_handlers
from .pay_in_bus import register_pay_in_bus_handlers
from .see_bus import register_see_bus_handlers

def register_search_tickets_handlers(dp: Dispatcher):
    register_start_station_handlers(dp)
    register_end_staion_handlers(dp)
    register_finded_station_handlers(dp)
    register_route_date_handlers(dp)
    register_show_routes_handlers(dp)
    register_see_route_handlers(dp)
    register_get_passengers_handlers(dp)
    register_pay_handlers(dp)
    register_pay_in_bus_handlers(dp)
    register_see_bus_handlers(dp)
