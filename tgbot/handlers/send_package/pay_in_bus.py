import io
import json

from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.types import Message, ContentType, CallbackQuery
from aioredis import Redis
from aiogram import types
from aiogram.contrib.middlewares.i18n import I18nMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from tgbot.handlers.send_package.pay import add_remind_to_package
from tgbot.handlers.start import start_handler_for_registered
from tgbot.services import db
from tgbot.keyboards import inline
from tgbot.services.ticket_generator.main import TicketGenerator


async def pay_for_package_in_bus(
    call: CallbackQuery,
    callback_data: dict,
    redis: Redis,
    ticket_generator: TicketGenerator,
    i18n: I18nMiddleware,
    state: FSMContext,
    scheduler: AsyncIOScheduler,
):
    await call.answer()
    payment_message_id = await redis.get(
        f'ticket_payment_message_id:{call.from_user.id}'
    )
    await call.bot.delete_message(
        chat_id=call.from_user.id,
        message_id=payment_message_id.decode(),
    )
    package_info = json.loads(
        await redis.get(callback_data['redis_key'])
    )
    package_id = await db.create_package(
        telegram_id=call.from_user.id,
        route_id=package_info['route_id'],
        start_station_id=package_info['start_station_id'],
        end_station_id=package_info['end_station_id'],
        is_paid=False,
        sender_full_name=package_info['sender_full_name'],
        sender_phone_number=package_info['sender_phone'],
        receiver_full_name=package_info['receiver_full_name'],
        receiver_phone_number=package_info['receiver_phone'],
    )
    package = await db.get_package(package_id)
    await call.bot.send_message(
        chat_id=call.from_user.id,
        text=i18n.gettext(
            '<i><b>Дякуємо за ваше замовлення👌🏻</b>\n'
            '(всі квитки зберігаються в розділі "мої квитки")\n\n'
            '<b>Ваша накладна 👇🏻</b></i>'
        )
    )
    package_image_bytes = await ticket_generator.generate_package(package)
    
    await call.bot.send_photo(
        chat_id=call.from_user.id,
        photo=types.input_file.InputFile(
            io.BytesIO(package_image_bytes),
        )
    )
    await add_remind_to_package(
        bot=call.bot,
        package_id=package_id,
        i18n=i18n,
        scheduler=scheduler,
    )
    await start_handler_for_registered(
        call.message, i18n, state, call.bot['config']
    )


def register_pay_in_bus_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        pay_for_package_in_bus,
        inline.pay_for_package_callback.filter(),
    )
