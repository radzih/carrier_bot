import logging

from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.types import Message
from aiogram.contrib.middlewares.i18n import I18nMiddleware

from tgbot.keyboards import inline
from tgbot.services import db
from tgbot.misc import states


async def get_station_name_from_message(
    message: Message,
    i18n: I18nMiddleware,
    state: FSMContext,
):
    finded_stations = await db.search_station_by_name(
        message.text,
        telegram_id=message.from_user.id,
    )
    if finded_stations:
        text = finded_stations_text(i18n)
        markup = inline.finded_stations_markup(i18n, finded_stations)
    else: 
        popular_stations = await db.get_popular_stations(
        message.from_user.id,
        )
        text = not_finded_stations_text(i18n)
        markup = inline.popular_stations_markup(popular_stations, i18n)
    await message.answer(
        text=text,
        reply_markup=markup,
    )


def finded_stations_text(i18n: I18nMiddleware):
    return i18n.gettext(
        'Оберіть з переліку нижче станцію 👇'
    )

def not_finded_stations_text(i18n: I18nMiddleware):
    return i18n.gettext(
        '❎ <b>Така станція не знайдена!</b>\n\n'
        'Напишіть ще раз її назву.\n\n'
        'Або почніть новий пошук.\n\n'
        'Або оберіть з переліку нижче станцію 👇\n'
    )


def register_finded_station_handlers(dp: Dispatcher):
    dp.register_message_handler(
        get_station_name_from_message,
        state=[
            states.SelectPackage.get_start_station,
            states.SelectPackage.get_end_station,
        ],
    )