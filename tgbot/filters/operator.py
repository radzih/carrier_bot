import typing

from aiogram.dispatcher.filters import BoundFilter

from tgbot.services import db
from tgbot.misc import schemas

class OperatorFilter(BoundFilter):
    key = 'is_operator'

    def __init__(self, is_operator: typing.Optional[bool] = None):
        self.is_operator = is_operator

    async def check(self, obj):
        if self.is_operator is None:
            return False
        operators: list[schemas.Operator] = await db.get_operators()
        operators_ids = [operator.telegram_id for operator in operators]
        return (obj.from_user.id in operators_ids) == self.is_operator
