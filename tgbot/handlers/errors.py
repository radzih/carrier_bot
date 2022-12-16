from aiogram.dispatcher import Dispatcher
from aiogram.types import Update
from aiogram.utils.exceptions import MessageNotModified

from tgbot.misc.exceptions import *
from web.app import models


async def support_confirmed_by_other(
    update: Update,
    exception: models.SupportRequest.DoesNotExist,
    ) -> bool:
    message = update.callback_query.message.text
    await update.callback_query.message.edit_text(
        text=message +(
            '\nКлієнт віключився від розмови, або інший оператор вже відповів.'
        )
    )
    return True

async def message_not_modified(
    update: Update,
    exception: MessageNotModified,
) -> bool:
    # return True
    return False
    

def register_error_handlers(dp: Dispatcher):
    dp.register_errors_handler(
        callback=support_confirmed_by_other,
        exception=models.SupportRequest.DoesNotExist,
    )
    dp.register_errors_handler(
        callback=message_not_modified,
        exception=MessageNotModified,
    )
    