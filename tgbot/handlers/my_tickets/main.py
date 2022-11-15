from aiogram.dispatcher import Dispatcher
from aiogram.types import CallbackQuery
from aiogram.contrib.middlewares.i18n import I18nMiddleware
    
from tgbot.keyboards import inline
from tgbot.misc import schemas
from tgbot.services import db


async def show_main(
    call: CallbackQuery,
    i18n: I18nMiddleware,
):
    await call.answer()
    if call.message.photo:
        await call.message.delete()
        answer = call.message.answer
    else:
        answer = call.message.edit_text

    valid_tickets: list[schemas.Ticket] = await db.get_user_valid_tickets(
        telegram_id=call.from_user.id,
    )
    archive_tickets: list[schemas.Ticket] = await db.get_user_archive_tickets(
        telegram_id=call.from_user.id,
    )
    valid_packages: list[schemas.Package] = await db.get_user_valid_packages(
        telegram_id=call.from_user.id,
    )
    archive_packages: list[schemas.Package] = await db.get_user_archive_packages(
        telegram_id=call.from_user.id,
    )

    await answer(
        text=i18n.gettext(
            '🎫📦 <b><i>Ваші замовлення</i></b> 📦🎫\n\n'
            '<b>-------------------------------------------</b>\n\n'
            '🎫 <b>Квитків:</b> {valid_tickets}\n'
            '📦 <b>Посилок:</b> {valid_packages}\n\n'
            '<b>-------------------------------------------</b>\n\n'
            '🗂 <b><i>В архіві</i></b>\n\n'
            '<b>---</b>\n\n'
            '🎫 <b>Квитків:</b> {archive_tickets}\n'
            '📦 <b>Посилок:</b> {archive_packages}\n'
        ).format(
            valid_tickets=len(valid_tickets),
            valid_packages=len(valid_packages),
            archive_tickets=len(archive_tickets),
            archive_packages=len(archive_packages),
        ),

        reply_markup=inline.my_tickets_menu(i18n),
    )


def register_main_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        show_main,
        text='my_tickets',
    )
