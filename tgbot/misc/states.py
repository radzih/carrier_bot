from aiogram.dispatcher.filters.state import StatesGroup, State


class SelectTicket(StatesGroup):
    get_start_station = State()
    get_end_station = State()
    get_route_date = State()
    get_passengers_amount = State()
    get_passenger_ticket_type = State()
    get_passenger_full_name = State()
    get_passenger_phone = State()
    
class SelectPackage(StatesGroup):
    get_start_station = State()
    get_end_station = State()
    get_route_date = State()
    get_sender_full_name = State()
    get_sender_phone = State()
    get_receiver_full_name = State()
    get_receiver_phone = State()
       