import typing

from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import Message

from tgbot.services import db


class IsRegisteredFilter(BoundFilter):
    key = 'is_registered'

    def __init__(self, is_registered: typing.Optional[bool] = None):
        self.is_registered = is_registered

    async def check(self, obj: Message) -> bool:
        if self.is_registered is None:
            return False
        is_in_database = await db.is_telegram_user_registered(obj.from_user.id)
        return is_in_database == self.is_registered
    