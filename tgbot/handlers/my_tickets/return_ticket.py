from aiogram.dispatcher import Dispatcher
from aiogram.types import CallbackQuery
from aiogram.contrib.middlewares.i18n import I18nMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.base import JobLookupError

from tgbot.keyboards import inline
from tgbot.services import db
from tgbot.misc import schemas
from tgbot.services import liqpay
from tgbot.config import Config


async def return_paid_ticket(
    call: CallbackQuery,
    callback_data: dict,
    config: Config,
    i18n: I18nMiddleware,
    scheduler: AsyncIOScheduler,
):
    await call.answer(cache_time=10)
    ticket_id = callback_data['ticket_id']
    ticket: schemas.Ticket = await db.get_ticket(ticket_id)
    await db.delete_ticket(ticket_id)
    payment: schemas.Payment = await liqpay.get_payment(
        payment_id=ticket.payment_id,
        public_key=config.liqpay.public_key,
        private_key=config.liqpay.private_key,
    )
    await liqpay.refund_money(
        order_id=payment.order_id,
        public_key=config.liqpay.public_key,
        private_key=config.liqpay.private_key,
        amount=payment.amount,
    )
    await call.message.delete()
    await call.message.answer(
        text=i18n.gettext(
            '❗ Ваш квиток успішно повернено ❗\n\n'
            'Гроші будуть зараховані на картку '
            '<b><i>{payment.sender_card_mask2}</i></b> впродовж 3 робочих днів.\n\n'
            '<b><i>Дякуємо, що обрали нашого перевізника!</i></b>'
        ).format(
            payment=payment
        ),
        reply_markup=inline.after_ticket_refund_markup(i18n),
    )
    remove_remind_about_route(scheduler, ticket.ticket_code)
    remove_recomend_play_game(scheduler, ticket.ticket_code)


def remove_remind_about_route(
    scheduler: AsyncIOScheduler,
    ticket_code: str,
):
    try: 
        scheduler.remove_job(
            f'remind_about_ticket_route:{ticket_code}',
        )
    except JobLookupError:
        pass
    
    try: 
        scheduler.remove_job(
            f'remind_about_ticket_route2:{ticket_code}',
        )
    except JobLookupError:
        pass
        

def remove_recomend_play_game(
    scheduler: AsyncIOScheduler,
    ticket_code: str,
):
    try: 
        scheduler.remove_job(
            f'play_game:{ticket_code}',
        )
    except JobLookupError:
        pass

async def return_not_paid_ticket(
    call: CallbackQuery,
    callback_data: dict,
    i18n: I18nMiddleware,
    scheduler: AsyncIOScheduler,
):
    ticket_id = callback_data['ticket_id']
    ticket: schemas.Ticket = await db.get_ticket(ticket_id)
    await db.delete_ticket(ticket_id)
    await call.message.delete()
    await call.message.answer(
        text=i18n.gettext(
            '❗ Ваш квиток успішно повернено ❗\n\n'
            '<b><i>Дякуємо, що обрали нашого перевізника!</i></b>'
        ),
        reply_markup=inline.after_ticket_refund_markup(i18n),
    )
    remove_remind_about_route(scheduler, ticket.ticket_code)
    remove_recomend_play_game(scheduler, ticket.ticket_code)

def register_return_ticket_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        return_paid_ticket,
        inline.return_ticket_callback.filter(
            is_paid='True',
        )
    )
    dp.register_callback_query_handler(
        return_not_paid_ticket,
        inline.return_ticket_callback.filter(
            is_paid='False',
        )
    )