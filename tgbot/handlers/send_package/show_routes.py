import logging
import math
import datetime

from aioredis import Redis
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.contrib.middlewares.i18n import I18nMiddleware

from tgbot.keyboards import reply, inline
from tgbot.misc import schemas, states
from tgbot.services import db
from tgbot.handlers.send_package.route_date import enter_route_date


async def show_routes(
    message: Message,
    state: FSMContext,
    i18n: I18nMiddleware,
    redis: Redis,
):
    if not message.text.count('.') or not message.text.replace('.', '').isdigit() or \
        message.text.split('.')[0].isdigit() and int(message.text.split('.')[0]) > 31 or \
            message.text.split('.')[1].isdigit() and int(message.text.split('.')[1]) > 12:
        return await message.answer(
            text=i18n.gettext(
                'Невірний формат дати. Спробуйте ще раз.'
            ),
        )

    day, month = message.text.split('.')
    date = datetime.datetime(
            year=datetime.date.today().year,
            day=int(day),
            month=int(month),
        )

    await state.finish()
    await message.answer(
        text=i18n.gettext(
            '🔍 Починаю пошук маршрутів...'
        ),
        reply_markup=reply.remove_kb,
    )

    chosen_route_data = schemas.ChosenRouteData.parse_raw(
        await redis.get(f'{message.from_user.id}:chosen_route_data')
    )

    routes = await db.get_routes_from_to_in_date(
        start_station_id=chosen_route_data.start_station.id,
        end_station_id=chosen_route_data.end_station.id,
        date=date,
        telegram_id=message.from_user.id,
    )
    ticket_types = await db.get_ticket_types(message.from_user.id)
    
    if not routes:
        await message.answer(
            text=i18n.gettext(
                'На жаль, на цю дату немає автобусів 😔'
                'Спробуйте ввести іншу дату.'
            ),
        )

    messages = generate_messages(routes, ticket_types, i18n, date)
    for i, message_send in enumerate(messages):
        if i == len(messages) - 1:
            await message.answer(
                text=''.join(message_send),
                reply_markup=inline.package_routes_markup(
                    i18n, chosen_route_data.end_station.id, date.strftime('%d.%m')
                )
            )
            continue
        await message.answer(
            text=''.join(message_send),
        )
    await state.finish()


def generate_messages(
    routes: list[schemas.Route], 
    ticket_types: list[schemas.TicketType],
    i18n: I18nMiddleware,
    date: datetime.datetime,
    ):
    messages = [
        i18n.gettext(
            'Знайдено {route_count} автобусів на {date} 😊\n\n'
            '〰️〰️〰️〰️〰️〰️〰️〰️\n\n'
        ).format(route_count=len(routes), date=date.strftime('%d.%m.%Y')),
    ]
    i = 0
    j = 0
    while routes: 
        route = routes.pop()
        messages.append(
            i18n.gettext(
                '🚌 {start_station} — {end_station}\n'
                '🕚 відправлення в {departure_time}\n'
                '🕙 прибуття в {arrival_time}\n'
                '🚏 Подивитись маршрут: {route_command}\n'
                '🚌 автобус: подивитись {bus_command}\n'
                '📦 ціна доставки: {price} грн\n'
                '👉 Відправити посилку: {command}\n\n'
                '〰️〰️〰️〰️〰️〰️〰️〰️'
            ).format(
                start_station=route.user_start_station.full_name,
                end_station=route.user_end_station.full_name,
                departure_time=route.user_departure_time.strftime('%d.%m.%Y %H:%M'),
                arrival_time=route.user_arrival_time.strftime('%d.%m.%Y %H:%M'),
                route_command=(
                    '/route_' +
                    route.user_start_station.code + route.user_end_station.code    
                    + route.code
                ),
                bus_command='/bus_' + route.bus.code,
                price=route.package_price,
                command=(
                    '/package_' + 
                    route.user_start_station.code + route.user_end_station.code    
                    + route.code
                )
            )
        )
        # messages = list(split(messages, 5))
    return messages

def split(list_a, chunk_size):
    for i in range(0, len(list_a), chunk_size):
        yield list_a[i:i + chunk_size]
        
        
def get_ticket_price(price: int, discount: int):
    return math.ceil(price - (price * discount / 100))


async def refresh_routes(
    call: CallbackQuery,
    redis: Redis,
    i18n: I18nMiddleware,
    state: FSMContext,
):
    await call.message.delete()
    call.message.from_user.id = call.from_user.id
    call.message.text = call.data.split(':')[1]
    await show_routes(
        message=call.message,
        state=state,
        i18n=i18n,
        redis=redis,
    )


async def change_stations(
    call: CallbackQuery,
    redis: Redis,
    i18n: I18nMiddleware,
    state: FSMContext,
):
    call.message.from_user.id = call.from_user.id
    chosen_route_data = schemas.ChosenRouteData.parse_raw(
        await redis.get(f'{call.from_user.id}:chosen_route_data')
    )
    chosen_route_data.start_station, chosen_route_data.end_station = \
        chosen_route_data.end_station, chosen_route_data.start_station
    await redis.set(
        '{telegram_id}:chosen_route_data'.format(telegram_id=call.from_user.id),
        chosen_route_data.json(),
    )
    await enter_route_date(
        call=call,
        i18n=i18n,
        callback_data={'station_id': chosen_route_data.end_station.id},
        redis=redis, 
    )


async def another_day(
    call: CallbackQuery,
    redis: Redis,
    i18n: I18nMiddleware,
    state: FSMContext,
):
    call.message.from_user.id = call.from_user.id
    chosen_route_data = schemas.ChosenRouteData.parse_raw(
        await redis.get(f'{call.from_user.id}:chosen_route_data')
    )
    await enter_route_date(
        call=call,
        i18n=i18n,
        callback_data={'station_id': chosen_route_data.end_station.id},
        redis=redis, 
    )



def register_show_routes_handlers(dp: Dispatcher):
    dp.register_message_handler(
        show_routes,
        state=states.SelectPackage.get_route_date,
    )
    dp.register_callback_query_handler(
        refresh_routes,
        regexp=r'\Apackage_refresh_routes:\d{2}.\d{2}',
    )
    dp.register_callback_query_handler(
        another_day,
        text='package_another_day',
    )
    dp.register_callback_query_handler(
        change_stations,
        text='package_change_stations',
    )