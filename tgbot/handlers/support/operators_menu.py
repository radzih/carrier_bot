from aiogram.dispatcher import Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.contrib.middlewares.i18n import I18nMiddleware

from tgbot.keyboards import inline


async def show_operators_menu_handler(message: Message, i18n: I18nMiddleware):
    await message.delete()
    await message.answer(
        text='Натискайте кнопку',
        reply_markup=inline.operators_menu_markup(i18n),
    )
async def show_operators_menu_handler_call(
    call: CallbackQuery,
    i18n: I18nMiddleware,
):
    await call.message.edit_text(
        text='Натискайте кнопку',
        reply_markup=inline.operators_menu_markup(i18n),
    )


def register_operators_menu_handlers(dp: Dispatcher):
    dp.register_message_handler(
        show_operators_menu_handler,
        commands=['menu'],
        is_admin=True
    )
    dp.register_callback_query_handler(
        show_operators_menu_handler_call,
        text='operators_menu',
    )