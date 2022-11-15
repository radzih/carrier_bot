from aiogram.dispatcher import Dispatcher

from .delete_messages_via_bot import register_delete_messages_via_bot
from .cancel_callback import register_cancel_handlers


def register_system_handlers(dp: Dispatcher):
    register_cancel_handlers(dp)
    register_delete_messages_via_bot(dp)