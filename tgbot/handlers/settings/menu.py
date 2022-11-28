from aiogram.dispatcher import Dispatcher
from aiogram.types import CallbackQuery
from aiogram.contrib.middlewares.i18n import I18nMiddleware

from tgbot.keyboards import inline


async def go_to_menu(
    call: CallbackQuery,
    i18n: I18nMiddleware,
):
    await call.answer()
    await call.message.answer(
        text=i18n.gettext('Щоб продовжити роботу з ботом, поверніться до головного меню'),
        reply_markup=inline.go_to_menu_cross_button_markup
    )


def register_menu_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        go_to_menu,
    )