from aiogram.dispatcher import Dispatcher
from aiogram.types import CallbackQuery
from aiogram.contrib.middlewares.i18n import I18nMiddleware

from tgbot.keyboards import inline


async def select_archive(
    call: CallbackQuery,
    i18n: I18nMiddleware,
):
    await call.answer()
    if call.message.photo:
        await call.message.delete()
        await call.message.answer(
            text=i18n.gettext(
                '<b>Виберіть архів</b>'
            ), 
            reply_markup=inline.archive_markup(i18n),
        )
    else: 
        await call.message.edit_text(
            text=i18n.gettext(
                '<b>Виберіть архів</b>'
            ), 
            reply_markup=inline.archive_markup(i18n),
        )


def register_archive_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        select_archive,
        text='archive',
    )