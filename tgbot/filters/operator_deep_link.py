import typing
import uuid

from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import Message

from tgbot.services import db


class OperatorDeepLink(BoundFilter):
    key = 'is_operator_deep_link'

    def __init__(self, is_operator_deep_link: typing.Optional[bool] = None):
        self.is_operator_deep_link = is_operator_deep_link

    async def check(self, obj: Message):
        if self.is_operator_deep_link is None or not obj.get_args():
            return False
        try:
            user_uuid = uuid.UUID(obj.get_args())
        except ValueError:
            return False
        operators_uuids = await db.get_all_operator_confirm_uuids()
        return user_uuid in operators_uuids

