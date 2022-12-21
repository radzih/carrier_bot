from aioredis import Redis
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.contrib.middlewares.i18n import I18nMiddleware

from tgbot.keyboards import inline
from tgbot.misc import states, schemas
from tgbot.services import db


async def enter_end_station_callback(
    call: CallbackQuery,
    i18n: I18nMiddleware,
    callback_data: dict,
    redis: Redis
): 
    await call.answer()
    start_station: schemas.Station = await db.get_station(int(callback_data['station_id']), call.from_user.id)
    await db.add_start_station_to_users_search_history(
        call.from_user.id, start_station.id
    )

    await call.message.edit_text(
        text=i18n.gettext(
            '🚉 Станція відправлення: {start_station}\n\n'
        ).format(start_station=start_station.full_name),
    )

    chosen_route_data: schemas.ChosenRouteData = \
        schemas.ChosenRouteData.parse_raw(
            await redis.get(f'{call.from_user.id}:chosen_route_data')
        )
        
    chosen_route_data.start_station = start_station
    await redis.set(
        name=f'{call.from_user.id}:chosen_route_data',
        value=chosen_route_data.json()
    )

    user_station_history = await db.get_user_search_end_station_history(
        call.from_user.id
    )
    popular_stations = await db.get_popular_stations(call.from_user.id)

    stations_t = list(set(user_station_history[:2] + popular_stations))
    stations = []
    for station in stations_t:
        for s in stations:
            if s.name == station.name:
                continue
            stations.append(s)
         
    
 
    stations = [station for station in stations if station.id != start_station.id]
 
    await call.message.answer(
        text=i18n.gettext(
            '✍️ <b>Напишіть</b> станцію отримання!\n\n'
            'Наприклад: <b>Варна</b>\n\n'
            '👀 Або <b>оберіть</b> станцію\n\n'
        ),
        reply_markup=inline.user_station_history_markup(
            stations=stations,
        )
    )
    await states.SelectPackage.get_end_station.set()


def register_end_staion_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        enter_end_station_callback,
        inline.station_callback.filter(),
        state=states.SelectPackage.get_start_station,
    )
