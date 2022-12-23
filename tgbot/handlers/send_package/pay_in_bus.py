import io
import json
import datetime

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
    await call.bot.send_message(
        chat_id=call.bot.get("config").tg_bot.group_id,
        text=(
            '<b>Тип</b>: Посилка\n'
            f'<b>ПІБ відправника</b>: {package.sender.name} {package.sender.surname}'
            f'<b>Номер телефону</b>: {package.sender.phone}'
            f'<b>Час купівлі</b>: {datetime.datetime.now()}\n'
            f'<b>Дата відправлення</b>: {package.departure_time.strftime("%d.%m.%Y")}\n'
            f'<b>Час відправлення</b>: {package.departure_time.strftime("%H:%M")}\n'
            f'<b>Дата прибуття</b>: {package.arrival_time.strftime("%d.%m.%Y")}\n'
            f'<b>Час прибуття</b>: {package.arrival_time.strftime("%H:%M")}\n'
            f'<b>Станція відправлення</b>: {package.start_station.full_name}\n'
            f'<b>Станція прибуття</b>: {package.end_station.full_name}\n'
            f'<b>ПІБ отримувача</b>: {package.receiver.name} {package.receiver.surname}'
            f'<b>Номер телефону</b>: {package.receiver.phone}'
            f'<b>Вартість</b>: {package.price} грн\n'
            f'<b>Оплачено</b>: {"Так" if package.is_paid else "Ні"}\n'
            '\n'
            '<b>Замовник</b>:\n'
            f'<b>ПІБ</b>: {package.owner.full_name}\n'
            f'<b>Номер телефону</b>: {package.owner.phone}\n'
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
