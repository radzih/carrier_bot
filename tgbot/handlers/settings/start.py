from aiogram.dispatcher import Dispatcher
from aiogram.types import CallbackQuery
from aiogram.contrib.middlewares.i18n import I18nMiddleware

from tgbot.keyboards import inline


async def show_settings(
    call: CallbackQuery,
    i18n: I18nMiddleware,
):
    await call.answer()
    await call.message.edit_text(
        text=i18n.gettext(
            '<b>⚙ Налаштування ⚙\n'
            '----------------------------</b>'
        ),
        reply_markup=inline.settings_markup(i18n),
    )



def register_start_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        show_settings,
        text='settings',
    )