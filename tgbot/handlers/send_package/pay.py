import json
import io
import datetime

from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.types import Message, PreCheckoutQuery
from aioredis import Redis
from aiogram import types
from aiogram.contrib.middlewares.i18n import I18nMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.base import JobLookupError


from tgbot.services import db
from tgbot.misc import schemas
from tgbot.keyboards import inline
from tgbot.services.ticket_generator.main import TicketGenerator
from tgbot.handlers.send_package.payloads import package_payment_payload


async def confirm_payment(
    pre_check: PreCheckoutQuery,
    invoice_payload: dict,
    i18n: I18nMiddleware,
    redis: Redis,
):
    package_info = json.loads(
        await redis.get(invoice_payload['redis_key'])
    )
    is_route_started = await db.is_route_started(
        package_info['route_id'], package_info['start_station_id']
    )
    if is_route_started:
        await pre_check.bot.answer_pre_checkout_query(
            pre_checkout_query_id=pre_check.id,
            ok=False,
            error_message=i18n.gettext("Вибачте але автобус вже відправився"),
        )
        return False

    await pre_check.bot.answer_pre_checkout_query(
        pre_checkout_query_id=pre_check.id,
        ok=True,
    )

    
async def successfull_payment_for_package(
    message: Message,
    invoice_payload: dict,
    redis: Redis,
    ticket_generator: TicketGenerator,
    i18n: I18nMiddleware,
    scheduler: AsyncIOScheduler,
):
    payment_message_id = await redis.get(
        f'ticket_payment_message_id:{message.from_user.id}'
    )
    await message.bot.delete_message(
        chat_id=message.from_user.id,
        message_id=payment_message_id.decode(),
    )
    package_info = json.loads(
        await redis.get(invoice_payload['redis_key'])
    )
    package_id = await db.create_package(
        telegram_id=message.from_user.id,
        route_id=package_info['route_id'],
        start_station_id=package_info['start_station_id'],
        end_station_id=package_info['end_station_id'],
        is_paid=True,
        payment_id=message.successful_payment.provider_payment_charge_id,
        sender_full_name=package_info['sender_full_name'],
        sender_phone_number=package_info['sender_phone'],
        receiver_full_name=package_info['receiver_full_name'],
        receiver_phone_number=package_info['receiver_phone'],
    )
    package = await db.get_package(package_id)
    await message.bot.send_message(
        chat_id=message.from_user.id,
        text=i18n.gettext(
            '<i><b>Дякуємо за ваше замовлення👌🏻</b>\n'
            '(всі квитки зберігаються в розділі "мої квитки")\n\n'
            '<b>Ваша накладна 👇🏻</b></i>'
        )
    )
    package_image_bytes = await ticket_generator.generate_package(package)
    
    await message.bot.send_photo(
        chat_id=message.from_user.id,
        photo=types.input_file.InputFile(
            io.BytesIO(package_image_bytes),
        )
    )

    await add_remind_to_package(
        bot=message.bot,
        package_id=package_id,
        i18n=i18n,
        scheduler=scheduler,
    )


async def add_remind_to_package(
    bot: Bot,
    package_id: int,
    scheduler: AsyncIOScheduler,
    i18n: I18nMiddleware,
):
    package: schemas.Package = await db.get_package(package_id)
    try:
        scheduler.remove_job(f"remind_about_package_route:{package.package_code}")
        scheduler.remove_job(f"remind_about_package_route2:{package.package_code}")
    except JobLookupError:
        pass
    scheduler.add_job(
        remind_about_package_route,
        trigger='date',   
        run_date=package.departure_time - datetime.timedelta(hours=1),
        id=f'remind_about_package_route:{package.package_code}',
        kwargs={
            'package_id': package_id,
        }
    )
    scheduler.add_job(
        remind_about_package_route,
        trigger='date',   
        run_date=package.departure_time - datetime.timedelta(hours=3),
        id=f'remind_about_package_route2:{package.package_code}',
        kwargs={
            'package_id': package_id,
        }
    )


async def remind_about_package_route(
    bot: Bot,
    package_id: int,
):
    URL = 'https://maps.google.com/?q={latitude},{longitude}'
    i18n: I18nMiddleware = bot.get('i18n')
    package: schemas.Package = await db.get_package(package_id)
    if not package.owner.is_notifications_enabled:
        return
    await bot.send_message(
        chat_id=package.owner.telegram_id,
        text=i18n.gettext(
            '<i><b>Нагадуємо про вашу поїздку через годину</b></i>\n',
            locale=package.owner.language.code
        ),
        reply_markup=inline.link_to_start_station(
            i18n=i18n,
            url=URL.format(
                latitude=package.start_station.laititude,
                longitude=package.start_station.longitude,
            )
        )
    )



def register_pay_handlers(dp: Dispatcher):
    dp.register_pre_checkout_query_handler(
        confirm_payment,
        package_payment_payload.filter(),
    )
    dp.register_message_handler(
        successfull_payment_for_package,
        package_payment_payload.filter(),
        content_types=['successful_payment'],
    )