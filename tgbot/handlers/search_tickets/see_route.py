import re
import logging

from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.dispatcher.filters.builtin import RegexpCommandsFilter
from aiogram.contrib.middlewares.i18n import I18nMiddleware

from tgbot.keyboards import inline
from tgbot.misc import schemas
from tgbot.services import db


async def show_route_stations(
    message: Message,
    i18n: I18nMiddleware,
    state: FSMContext,
    regexp_command: re.Match,
): 
    await state.finish()
    ( 
        start_station_code,
        end_station_code,
        route_code,
    ) = regexp_command.groups()

    route_stations = await db.get_route_from_to_stations(
        start_station_code,
        end_station_code,
        route_code,
        message.from_user.id,
    )


    text = generate_route_stations_message(route_stations, i18n)
    
    await message.answer(
        text=text,
        reply_markup=inline.close_markup,
    )
    

def generate_route_stations_message(
    stations: list[schemas.Station],
    i18n: I18nMiddleware,
) -> str:
    result = []
    for station in stations:
        result.append(
            i18n.gettext(
                '🚌 {name}\n'
                '🕖 відправлення в: {departure_time}\n'
                '〰️〰️〰️〰️〰️〰️〰️〰️\n'
            ).format(
                name=station.full_name,
                departure_time=station.departure_time.strftime('%Y-%m-%d %H:%M')
            )
        )
    return ''.join(result)
    



def register_see_route_handlers(dp: Dispatcher):
    dp.register_message_handler(
        show_route_stations,
        RegexpCommandsFilter(
            regexp_commands=[r'/route_(\w{4})(\w{4})(\w{6})$', ]
        ),
        state='*',
    )