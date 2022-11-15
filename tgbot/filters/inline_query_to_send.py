import typing

from aiogram.dispatcher.filters import BoundFilter

from tgbot.services import db 



class InlineQueryToSend(BoundFilter):
    key = 'is_send_message'

    def __init__(self, is_send_message: typing.Optional[bool] = None):
        self.is_send_message = is_send_message

    async def check(self, obj):
        if not self.is_send_message or not obj.via_bot :
            return False
        users = await db.get_telegram_users()
        if obj.text in [user.full_name for user in users]:
            return True
        return False

