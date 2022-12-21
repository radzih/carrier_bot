from aioredis import Redis
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.contrib.middlewares.i18n import I18nMiddleware

from tgbot.services import db
from tgbot.keyboards import inline
from tgbot.misc import states, schemas


async def enter_start_station_callback(
    call: CallbackQuery,
    i18n: I18nMiddleware,
    redis: Redis,
):
    await call.answer()
    await search_tickets(
        user_id=call.from_user.id,
        i18n=i18n,
        send_or_edit=call.message.edit_text,
        redis=redis,
    )

async def enter_start_station_message(
    message: Message,
    i18n: I18nMiddleware,
    redis: Redis,
    state: FSMContext,
):
    await state.finish()
    await search_tickets(
        user_id=message.from_user.id,
        i18n=i18n,
        send_or_edit=message.answer,
        redis=redis,
    )


async def search_tickets(
    user_id: int,
    i18n: I18nMiddleware,
    send_or_edit: callable,
    redis: Redis,
):
    user_station_history: list = await db.get_user_search_start_station_history(
        user_id
    )
    popular_stations = await db.get_popular_stations(
        user_id
    )

    stations= list(set(user_station_history[:2] + popular_stations))
 
    await redis.set(
        name=f'{user_id}:chosen_route_data',
        value=schemas.ChosenRouteData.create_empty().json()
    )


    await send_or_edit(
        text=i18n.gettext(
            '✍️ <b>Напишіть</b> станцію відправлення!\n'
            'Наприклад: <b>Одеса</b>\n\n'
            '👀 Або <b>оберіть</b> станцію\n'
        ),
        reply_markup=inline.user_station_history_markup(
            stations=stations,
        )
    )
    await states.SelectTicket.get_start_station.set()


def register_start_station_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        enter_start_station_callback,
        text='search_tickets',
    )
    dp.register_message_handler(
        enter_start_station_message,
        commands=['search'],
        exclude_states=['waiting_for_operator', 'support_conversation'],
        state='*',
    )
