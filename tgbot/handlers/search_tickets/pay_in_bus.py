from aiogram.dispatcher import Dispatcher
from aiogram.types import CallbackQuery
from aioredis import Redis
from aiogram.contrib.middlewares.i18n import I18nMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from tgbot.keyboards import inline
from tgbot.services import db
from tgbot.handlers.search_tickets.pay import send_tickets
from tgbot.services.ticket_generator.main import TicketGenerator
from tgbot.handlers.search_tickets.pay import add_remind_to_tickets, remind_game


async def pay_in_bus(
    call: CallbackQuery,
    callback_data: dict,
    redis: Redis,
    ticket_generator: TicketGenerator,
    i18n: I18nMiddleware,
    scheduler: AsyncIOScheduler,
):
    await call.answer()

    tickets_ids = [int(id) for id in callback_data['tickets_ids'].split('|')]
    for ticket_id in tickets_ids:
        await db.mark_ticket_as_pay_in_bus(
            ticket_id=ticket_id,
        )

    payment_message_id = await redis.get(
        f'ticket_payment_message_id:{call.from_user.id}'
    )
    await call.bot.delete_message(
        chat_id=call.from_user.id,
        message_id=payment_message_id.decode(),
    )
    
    await send_tickets(
        bot=call.bot,
        i18n=i18n,
        tickets_ids=tickets_ids,
        ticket_generator=ticket_generator,
        user_id=call.from_user.id,
    )
    await add_remind_to_tickets(
        bot=call.bot,
        ticket_ids=tickets_ids,
        i18n=i18n,
        scheduler=scheduler,
    )
    await remind_game(
        scheduler=scheduler,
        ticket_id=tickets_ids[0],
    )
    



def register_pay_in_bus_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        pay_in_bus,
        inline.pay_for_tickets_callback.filter()
    )