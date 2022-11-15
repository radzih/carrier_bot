from typing import Literal

from asgiref.sync import sync_to_async

from aiogram import types
from aiogram.contrib.middlewares.i18n import I18nMiddleware

from tgbot.services import db
from tgbot.misc import schemas


class LocaleMiddleware(I18nMiddleware):
    async def get_user_locale(
        self,
        action: str,
        args: tuple
    ) -> Literal['ru', 'uk']:
        user_telegram: types.User = types.User.get_current()
        try: 
            user: schemas.TelegramUser = \
                await db.get_telegram_user(user_telegram.id)
        except AttributeError:
            return user_telegram.language_code
        return user.language.code

        