from aiogram.dispatcher import Dispatcher
from aiogram import types


async def delete_message_via_bot(
    message: types.Message,
) -> None:
    await message.delete()


def register_delete_messages_via_bot(dp: Dispatcher):
    dp.register_message_handler(
        delete_message_via_bot,
        lambda message: message.via_bot.id == message.bot.id \
            if message.via_bot else False,
    )