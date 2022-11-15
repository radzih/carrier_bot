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


async def return_paid_package(
    call: CallbackQuery,
    callback_data: dict,
    config: Config,
    i18n: I18nMiddleware,
    scheduler: AsyncIOScheduler,
):
    await call.answer(cache_time=10)
    package_id = callback_data['package_id']
    package: schemas.Package = await db.get_package(package_id)
    await db.delete_package(package_id)
    payment: schemas.Payment = await liqpay.get_payment(
        payment_id=package.payment_id,
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
            '❗ Вашу відправку успішно скасовано❗\n\n'
            'Гроші будуть зараховані на картку '
            '<b><i>{mask}</i></b> впродовж 3 робочих днів.\n\n'
            '<b><i>Дякуємо, що обрали нашого перевізника!</i></b>'
        ).format(
            mask=payment.sender_card_mask2,
        ),
        reply_markup=inline.after_package_refund_markup(i18n),
    )
    remove_remind_about_route(
        scheduler=scheduler,
        ticket_code=package.package_code,
    )



async def return_not_paid_package(
    call: CallbackQuery,
    callback_data: dict,
    i18n: I18nMiddleware,
    scheduler: AsyncIOScheduler,
):
    package_id = callback_data['package_id']
    package = await db.get_package(package_id)
    await db.delete_package(package_id)
    await call.message.delete()
    await call.message.answer(
        text=i18n.gettext(
            '❗ Вашу відправку успішно повернено ❗\n\n'
            '<b><i>Дякуємо, що обрали нашого перевізника!</i></b>'
        ),
        reply_markup=inline.after_package_refund_markup(i18n),
    )
    remove_remind_about_route(
        scheduler=scheduler,
        ticket_code=package.package_code,
    )


def remove_remind_about_route(
    scheduler: AsyncIOScheduler,
    ticket_code: str,
):
    try: 
        scheduler.remove_job(
            f'remind_about_package_route:{ticket_code}',
        )
    except JobLookupError:
        pass
    
    try: 
        scheduler.remove_job(
            f'remind_about_package_route2:{ticket_code}',
        )
    except JobLookupError:
        pass

def register_return_package_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        return_paid_package,
        inline.return_package_callback.filter(
            is_paid='True',
        )
    )
    dp.register_callback_query_handler(
        return_not_paid_package,
        inline.return_package_callback.filter(
            is_paid='False',
        )
    )