from aiogram.dispatcher import Dispatcher
from aiogram.types import CallbackQuery


async def cancel(call: CallbackQuery):
    await call.message.delete()


def register_cancel_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        cancel,
        text='cancel',
        state='*',
    )