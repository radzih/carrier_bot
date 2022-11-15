from aiogram.dispatcher import Dispatcher
from aiogram.types import CallbackQuery
from aiogram.contrib.middlewares.i18n import I18nMiddleware

from tgbot.keyboards import inline
from tgbot.services import db
from tgbot.misc import schemas


NOTIFICATION_EMOJI = {
    True: '🔔',
    False: '🔕',
}


async def turn_notifications(
    call: CallbackQuery,
    i18n: I18nMiddleware,
):
    await call.answer()
    if call.data == 'turn_notifications':
        await db.turn_notifications(call.from_user.id)
    user: schemas.TelegramUser = await db.get_telegram_user(call.from_user.id)
    await call.message.edit_text(
        text=i18n.gettext(
            '{emoji} '
            f'<b>Нагадування</b>'
            ' {emoji}\n'
            f'<b>----------------------------</b>\n'
            f'<i>Наразі нагадування</i> '
            '<b>{status}</b>'
        ).format(
            emoji=NOTIFICATION_EMOJI[user.is_notifications_enabled],
            status='вкл.' if user.is_notifications_enabled else 'викл.',
        ), 
        reply_markup=inline.turn_notifications_markup(i18n)
    )


def register_notifications_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        turn_notifications,
        text='notifications',
    )
    dp.register_callback_query_handler(
        turn_notifications,
        text='turn_notifications',
    )