from aiogram.dispatcher import Dispatcher
from aiogram.types import CallbackQuery
from aiogram.contrib.middlewares.i18n import I18nMiddleware

from tgbot.keyboards import inline
from tgbot.services import db
from tgbot.misc import schemas


async def select_language(
    call: CallbackQuery,
    i18n: I18nMiddleware,
): 
    await call.answer()
    user: schemas.TelegramUser = await db.get_telegram_user(call.from_user.id)
    languages: list[schemas.Language] = await db.get_languages()
    await call.message.edit_text(
        text=i18n.gettext(
            '<b>🌐 Оберіть мову 🌐\n'
            '----------------------------\n\n</b>'
            '<i>Поточна мова -</i> <b>{user.language.name}</b>',
            locale=user.language.code,
        ).format(
            user=user
        ), 
        reply_markup=inline.languages_markup(languages),
    )

async def set_language(
    call: CallbackQuery,
    callback_data: dict[str, str],
    i18n: I18nMiddleware,
):
    await call.answer()
    language_id = int(callback_data['language_id'])
    languages: list[schemas.Language] = await db.get_languages()
    await db.set_language_to_user(
        telegram_id=call.from_user.id,
        language_id=language_id,
    )
    user: schemas.TelegramUser = await db.get_telegram_user(call.from_user.id)
    await call.message.edit_text(
        text=i18n.gettext(
            '<b>🌐 Мова успішно змінена 🌐\n'
            '----------------------------\n\n</b>'
            '<i>Поточна мова -</i> <b>{user.language.name}</b>',
            locale=user.language.code,
        ).format(
            user=user
        ),
        reply_markup=inline.languages_markup(languages),
    )


def register_language_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        select_language,
        text='language',
    )
    dp.register_callback_query_handler(
        set_language,
        inline.set_language_callback.filter(),
    )