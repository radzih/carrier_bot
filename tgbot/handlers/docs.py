from aiogram.dispatcher import Dispatcher
from aiogram.types import Message
from aiogram.contrib.middlewares.i18n import I18nMiddleware

from tgbot.keyboards import inline


async def show_docs(
    message: Message,
    i18n: I18nMiddleware,
):
    await message.answer(
        text=i18n.gettext(
            'Натисність на кнопку щоб відкрити договір публічної оферти'
        ),
        reply_markup=inline.public_ofert(i18n)
    )


def register_docs_handlers(dp: Dispatcher):
    dp.register_message_handler(
        show_docs,
        commands=['docs']
    )