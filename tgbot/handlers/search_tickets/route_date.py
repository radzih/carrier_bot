from aioredis import Redis
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.types import CallbackQuery
from aiogram.contrib.middlewares.i18n import I18nMiddleware

from tgbot.misc import schemas, states
from tgbot.services import db
from tgbot.keyboards import reply, inline


async def enter_route_date(
    call: CallbackQuery,
    i18n: I18nMiddleware,
    callback_data: dict,
    state: FSMContext,
    redis: Redis,
):

    end_station: schemas.Station = await db.get_station(
        int(callback_data['station_id']),
        call.from_user.id
    )

    chosen_route_data: schemas.ChosenRouteData = \
        schemas.ChosenRouteData.parse_raw(
            await redis.get(f'{call.from_user.id}:chosen_route_data')
        )
    chosen_route_data.end_station = end_station

    routes = await db.get_routes_from_to_with_available_seats(
        start_station_id=chosen_route_data.start_station.id,
        end_station_id=chosen_route_data.end_station.id,
    )

    await call.answer()
    await call.message.edit_text(
        text=i18n.gettext(
            '🚉 Станція відправлення: {start_station}\n\n'
        ).format(start_station=chosen_route_data.start_station.full_name),
    )
    await call.message.answer(
        text=i18n.gettext(
            '🚉 Станція прибуття: {end_station}\n\n'
        ).format(end_station=chosen_route_data.end_station.full_name),
    )
    if not routes: 
        await state.finish()
        return await call.message.answer(
            text=i18n.gettext(
                'На жаль, на даний момент, маршрутів з '
                'вибраними станціями не знайдено.\n\n'
                'Спробуйте вибрати інші станції.'
            ),
            reply_markup=inline.search_tickets_markup(i18n),
        )
    await call.message.answer(
        text=i18n.gettext(
            'Тепер напишіть дату поїздки в форматі '
            'день.місяць (наприклад: 01.02) або оберіть '
            'зі списку нижче 👇'
        ),
        reply_markup=reply.route_dates_markup(routes=routes),
    )
    await redis.set(
        name=f'{call.from_user.id}:chosen_route_data',
        value=chosen_route_data.json()
    )
    await db.add_end_station_to_users_search_history(
        call.from_user.id, end_station.id
    )
    await states.SelectTicket.get_route_date.set()


def register_route_date_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        enter_route_date,
        inline.station_callback.filter(),
        state=states.SelectTicket.get_end_station,
    )
