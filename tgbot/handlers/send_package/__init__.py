from aiogram.dispatcher import Dispatcher, FSMContext

from .end_station import register_end_staion_handlers
from .start_station import register_start_station_handlers
from .finded_station import register_finded_station_handlers
from .route_date import register_route_date_handlers
from .show_routes import register_show_routes_handlers
from .get_sender import register_get_sender_handlers
from .get_receiver import register_get_receiver_handlers
from .pay import register_pay_handlers
from .pay_in_bus import register_pay_in_bus_handlers

def register_send_package_handlers(dp: Dispatcher):
    register_get_sender_handlers(dp)
    register_start_station_handlers(dp)
    register_end_staion_handlers(dp)
    register_finded_station_handlers(dp)
    register_route_date_handlers(dp)
    register_show_routes_handlers(dp)
    register_get_receiver_handlers(dp)
    register_pay_handlers(dp)
    register_pay_in_bus_handlers(dp)
