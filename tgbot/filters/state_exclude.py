import typing
import inspect

from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher.filters.builtin import StateFilter
from contextvars import ContextVar

from tgbot.config import Config


class StatesExcludeFilter(BoundFilter):
    key='exclude_states'

    ctx_state = ContextVar('user_state')

    def __init__(self, dispatcher, exclude_states: typing.List[str]):
        from aiogram.dispatcher.filters.state import State, StatesGroup

        self.dispatcher = dispatcher
        states = []
        if not isinstance(exclude_states, (list, set, tuple, frozenset)) or exclude_states is None:
            exclude_states = [exclude_states, ]
        for item in exclude_states:
            if isinstance(item, State):
                states.append(item.state)
            elif inspect.isclass(item) and issubclass(item, StatesGroup):
                states.extend(item.all_states_names)
            else:
                states.append(item)
        self.exclude_states = states

    def get_target(self, obj):
        if isinstance(obj, CallbackQuery):
            return getattr(getattr(getattr(obj, 'message', None),'chat', None), 'id', None), getattr(getattr(obj, 'from_user', None), 'id', None)
        return getattr(getattr(obj, 'chat', None), 'id', None), getattr(getattr(obj, 'from_user', None), 'id', None)

    async def check(self, obj):
        try:
            state = self.ctx_state.get()
        except LookupError:
            chat, user = self.get_target(obj)

            if chat or user:
                state = await self.dispatcher.storage.get_state(chat=chat, user=user)
                self.ctx_state.set(state)
                if state in self.exclude_states:
                    return False

        else:
            if state in self.exclude_states:
                return False
        return {'state': self.dispatcher.current_state(), 'raw_state': state}
