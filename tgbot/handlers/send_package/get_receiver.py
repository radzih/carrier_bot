import re
import json

from aiogram.dispatcher import Dispatcher, FSMContext
from aioredis import Redis
from aiogram.types import Message
from aiogram.contrib.middlewares.i18n import I18nMiddleware
from aiogram import types

from tgbot.misc import states
from tgbot.services import db
from tgbot.keyboards import inline
from tgbot.config import Config
from tgbot.handlers.send_package.payloads import package_payment_payload


async def get_receiver_full_name_and_enter_receiver_phone(
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
        receiver_full_name=message.text,
    )
    await states.SelectPackage.get_receiver_phone.set()
    await message.answer(
        text=i18n.gettext(
            '📱 Напишіть номер телефону отримувача.\n'
            'Наприклад: +380501234567 \n'
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


async def get_receiver_phone(
    message: Message,
    i18n: I18nMiddleware,
    state: FSMContext,
    config: Config,
    redis: Redis,
):
    await state.update_data(
        receiver_phone=re.findall(r'\+380\d{9}$', message.text)[0],
    )
    state_data = await state.get_data()
    await state.finish()
    start_station = await db.get_station(
        state_data['route'].user_start_station.id,
        message.from_user.id,
    )
    end_station = await db.get_station(
        state_data['route'].user_end_station.id,
        message.from_user.id,
    )

    await message.answer(
        text=i18n.gettext(
            '📝Ваше замовлення📝\n'
            '🚌↗️ Відправлення:  {start_station}\n'
            '🚌↙️ Прибуття:  {end_station}\n'
            '🗓 Дата та час відправлення: {date}\n'
            '👥 ПІБ відправника:\n'
            '{sender_full_name}\n'
            '📱 Номер телефону відправника:\n'
            '{sender_phone}\n'
            '👥 ПІБ отримувача:\n'
            '{receiver_full_name}\n'
            '📱 Номер телефону отримувача:\n'
            '{receiver_phone}\n'
        ).format(
            sender_full_name=state_data['sender_full_name'],
            sender_phone=state_data['sender_phone'],
            receiver_full_name=state_data['receiver_full_name'],
            receiver_phone=state_data['receiver_phone'],
            start_station=start_station.full_name,
            end_station=end_station.full_name,
            date=state_data['route'].departure_time.strftime('%d.%m.%Y %H:%M'),
        )
    )
    await redis.set(
        f'{message.from_user.id}:package',
        json.dumps({
            'sender_full_name': state_data['sender_full_name'],
            'sender_phone': state_data['sender_phone'],
            'receiver_full_name': state_data['receiver_full_name'],
            'receiver_phone': state_data['receiver_phone'],
            'start_station_id': start_station.id,
            'end_station_id': end_station.id,
            'route_id': state_data['route'].id,
        }),
    )

    payment_message = await message.bot.send_invoice(
        chat_id=message.from_user.id,
        title=i18n.gettext('Покупка квитків'),
        description=i18n.gettext('Покупка квитків'),
        provider_token=config.tg_bot.payments_provider_token,
        currency='UAH',
        prices=[
            types.LabeledPrice(
                label=i18n.gettext('Покупка квитків'),
                amount=state_data['route'].package_price * 100,
            ),
        ],
        payload=package_payment_payload.new(
            redis_key=f'{message.from_user.id}:package',
        ),
        reply_markup=inline.pay_for_package_markup(
            i18n=i18n,
            redis_key=f'{message.from_user.id}:package',
        )
    )
    await redis.set(f'ticket_payment_message_id:{message.from_user.id}', payment_message.message_id)


def register_get_receiver_handlers(dp: Dispatcher):
    dp.register_message_handler(
        get_receiver_full_name_and_enter_receiver_phone,
        state=states.SelectPackage.get_receiver_full_name,
    )
    dp.register_message_handler(
        get_receiver_phone,
        state=states.SelectPackage.get_receiver_phone,
        regexp=r'\A\+380\d{9}$',
    )
    dp.register_message_handler(
        say_that_phone_wrong,
        state=[
            states.SelectPackage.get_receiver_phone,        
            states.SelectPackage.get_sender_phone,
        ],
    )