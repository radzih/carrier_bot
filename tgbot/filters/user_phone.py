import typing

from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import Message



class UserPhoneFilter(BoundFilter):
    key = 'is_user_phone'

    def __init__(self, is_user_phone: typing.Optional[bool] = None):
        self.is_user_phone = is_user_phone

    async def check(self, obj: Message):
        if self.is_user_phone is None:
            return False
        return obj.contact.user_id == obj.from_user.id
