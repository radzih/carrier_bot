import re

from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.contrib.middlewares.i18n import I18nMiddleware
from aiogram.dispatcher.filters.builtin import RegexpCommandsFilter

from tgbot.keyboards import inline
from tgbot.services import db
from tgbot.misc import states


async def enter_sender_full_name(
    message: Message,
    i18n: I18nMiddleware,
    regexp_command: re.Match,
    state: FSMContext,
):
    ( 
        start_station_code,
        end_station_code,
        route_code,
    ) = regexp_command.groups()

    route = await db.get_route(
        start_station_code,
        end_station_code,
        route_code,
    )

    await states.SelectPackage.get_sender_full_name.set()
    await message.answer(
        text=i18n.gettext(
            'Хто буде відправником?\n\n'
            '✍️ Напишіть Ім\'я та Прізвище.\n'
            'Наприклад: Тарас Шевченко \n'
        )
    )
    await state.update_data(
        route=route,
    )


async def get_sender_full_name_and_enter_sender_phone(
    message: Message,
    i18n: I18nMiddleware,
    state: FSMContext,
):
    if len(message.text.split(' ')) !=2:
        return await message.answer(
            text=i18n.gettext(
                '<b>Неправильний формат!</b>\n\n'
            )
        )
    await state.update_data(
        sender_full_name=message.text,
    )
    await states.SelectPackage.get_sender_phone.set()
    await message.answer(
        text=i18n.gettext(
            '📱 Напишіть номер телефону відправника.\n'
            'Наприклад: +380501234567 \n'
        )
    )


async def get_sender_phone_and_enter_receiver_full_name(
    message: Message,
    i18n: I18nMiddleware,
    state: FSMContext,
):
    phone = re.findall(r'\+380\d{9}', message.text)[0]
    await state.update_data(
        sender_phone=phone,
    )
    await states.SelectPackage.get_receiver_full_name.set()
    await message.answer(
        text=i18n.gettext(
            'Хто буде отримувачем?\n\n'
            '✍️ Напишіть Ім\'я та Прізвище.\n'
            'Наприклад: Іван Франко \n'
        )
    )


async def say_that_phone_wrong(
    message: Message,
    i18n: I18nMiddleware,
):
    await message.answer(
        text=i18n.gettext(
            '<b>Неправильний формат!</b>\n\n'
        )
    )


def register_get_sender_handlers(dp: Dispatcher):
    dp.register_message_handler(
        enter_sender_full_name,
        RegexpCommandsFilter(
            regexp_commands=[
                r'\A/package_(\w{4})(\w{4})(\w{6})$',
            ]
        ),    
        state='*',
    )
    dp.register_message_handler(
        get_sender_full_name_and_enter_sender_phone,
        state=states.SelectPackage.get_sender_full_name,
    )
    dp.register_message_handler(
        get_sender_phone_and_enter_receiver_full_name,
        state=states.SelectPackage.get_sender_phone,
        regexp=r'\+380\d{9}',
    )
    dp.register_message_handler(
        say_that_phone_wrong,
        state=states.SelectPackage.get_sender_phone,
    )