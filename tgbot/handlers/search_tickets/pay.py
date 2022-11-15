import datetime
import io
import logging
from aiogram import Bot

from aiogram.dispatcher  import Dispatcher
from aiogram.types import Message, PreCheckoutQuery, input_file
from aiogram.contrib.middlewares.i18n import I18nMiddleware
from aioredis import Redis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.base import JobLookupError

from tgbot.services import db
from tgbot.handlers.search_tickets.payloads import ticket_payment_payload
from tgbot.services.ticket_generator.main import TicketGenerator
from tgbot.misc import schemas
from tgbot.keyboards import inline


async def confirm_payment(
    pre_check: PreCheckoutQuery,
    invoice_payload: dict,
    i18n: I18nMiddleware,
    redis: Redis
):
    tickets_ids = map(int, invoice_payload["tickets_ids"].split('|'))
    for ticket_id in tickets_ids:
        if not await db.is_ticket_exists(ticket_id):
            await pre_check.answer(
                i18n.gettext("Вибачте але час бронювання вийшов"),
                show_alert=True,
            )
            return False
    await pre_check.bot.answer_pre_checkout_query(
        pre_checkout_query_id=pre_check.id,
        ok=True,
    )

async def succesfull_payment_for_ticket(
    message: Message,
    ticket_generator: TicketGenerator,
    i18n: I18nMiddleware,
    invoice_payload: dict,
    redis: Redis,
    scheduler: AsyncIOScheduler,
):
    payment_message_id = await redis.get(
        f"ticket_payment_message_id:{message.from_user.id}"
    )

    await message.bot.delete_message(
        chat_id=message.from_user.id,
        message_id=payment_message_id.decode(),
    )

    tickets_ids = [int(i) for i in invoice_payload['tickets_ids'].split('|')]
    for ticket_id in tickets_ids:
        await db.mark_ticket_as_paid(
            ticket_id=ticket_id,
            payment_id=message.successful_payment.provider_payment_charge_id,
        )

    await send_tickets(
        bot=message.bot,
        i18n=i18n,
        tickets_ids=tickets_ids,
        ticket_generator=ticket_generator,
        user_id=message.from_user.id,
    )

    await add_remind_to_tickets(
        bot=message.bot,
        ticket_ids=tickets_ids,
        i18n=i18n,
        scheduler=scheduler,
    )
    await remind_game(
        scheduler=scheduler,
        ticket_id=tickets_ids[0],
    )

async def remind_game(
    scheduler: AsyncIOScheduler,
    ticket_id: int,
):
    ticket: schemas.Ticket = await db.get_ticket(ticket_id)
    try: 
        scheduler.remove_job(f"play_game:{ticket.ticket_code}")
    except JobLookupError:
        pass 
    
    scheduler.add_job(
        recommend_to_play_game,
        trigger='date',
        id=f"play_game:{ticket.ticket_code}",
        run_date=ticket.departure_time + datetime.timedelta(minutes=5),
        kwargs={
            'user_id': ticket.owner.telegram_id,
        }
    )

async def add_remind_to_tickets(
    bot: Bot,
    ticket_ids: list[int],
    scheduler: AsyncIOScheduler,
    i18n: I18nMiddleware,
):
    for ticket_id in ticket_ids:
        ticket: schemas.Ticket = await db.get_ticket(ticket_id)
        try:
            scheduler.remove_job(f"remind_about_ticket_route:{ticket.ticket_code}")
            scheduler.remove_job(f"remind_about_ticket_route2:{ticket.ticket_code}")
        except JobLookupError:
            pass
        scheduler.add_job(
            remind_about_ticket_route,
            trigger='date',   
            run_date=ticket.departure_time - datetime.timedelta(hours=1),
            id=f'remind_about_ticket_route:{ticket.ticket_code}',
            kwargs={
                'ticket_id': ticket_id,
            }
        )
        scheduler.add_job(
            remind_about_ticket_route,
            trigger='date',   
            run_date=ticket.departure_time - datetime.timedelta(hours=3),
            id=f'remind_about_ticket_route2:{ticket.ticket_code}',
            kwargs={
                'ticket_id': ticket_id,
            }
        )



async def send_tickets(
    bot: Bot,
    i18n: I18nMiddleware,
    tickets_ids: list[int],
    ticket_generator: TicketGenerator,
    user_id: int,
):
    await bot.send_message(
        chat_id=user_id,
        text=i18n.gettext(
            '<i><b>Дякуємо за ваше замовлення👌🏻</b>\n'
            '(всі квитки зберігаються в розділі "мої квитки")\n\n'
            '<b>Ваші квитки 👇🏻</b></i>'
        )
    )

    for ticket_id in tickets_ids:
        ticket: schemas.Ticket = await db.get_ticket(ticket_id)
        ticket_image_bytes = await ticket_generator.generate_ticket(ticket)
        await bot.send_photo(
            chat_id=user_id,
                photo=input_file.InputFile(
                io.BytesIO(ticket_image_bytes),
            )
        )

        
async def recommend_to_play_game(
    bot: Bot,
    user_id: int,
):
    i18n: I18nMiddleware = bot.get('i18n')
    user = await db.get_telegram_user(user_id)
    await bot.send_message(
        chat_id=user_id,
        text=i18n.gettext(
            '<i>Хочеш зіграти в гру?</i>\n',
            locale=user.language.code,
        ),
        reply_markup=inline.play_game(
            i18n=i18n, game_link='https://poki.com/en/g/four-in-a-row', lk=user.language.code
        )
    )


async def remind_about_ticket_route(
    bot: Bot,
    ticket_id: int,
):
    URL = 'https://maps.google.com/?q={latitude},{longitude}'
    ticket: schemas.Ticket = await db.get_ticket(ticket_id)
    i18n = bot.get('i18n')
    if not ticket.owner.is_notifications_enabled:
        return
    await bot.send_message(
        chat_id=ticket.owner.telegram_id,
        text=i18n.gettext(
            '<i><b>Нагадуємо про вашу поїздку через годину</b></i>\n',
            locale=ticket.owner.language.code,
        ),
        reply_markup=inline.link_to_start_station(
            i18n=i18n,
            url=URL.format(
                latitude=ticket.start_station.laititude,
                longitude=ticket.start_station.longitude,
            )
        )
    )


def register_pay_handlers(dp: Dispatcher):
    dp.register_pre_checkout_query_handler(
        confirm_payment,
        ticket_payment_payload.filter()
    )
    dp.register_message_handler(
        succesfull_payment_for_ticket,
        ticket_payment_payload.filter(),
        content_types=['successful_payment'],
    )