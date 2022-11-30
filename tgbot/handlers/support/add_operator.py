import uuid

from aiogram.dispatcher import Dispatcher
from aiogram.types import Message, CallbackQuery, BotCommand, BotCommandScope
from aiogram.utils.deep_linking import get_start_link
from aiogram.contrib.middlewares.i18n import I18nMiddleware


from tgbot.keyboards import inline
from tgbot.misc import schemas
from tgbot.services import db
from tgbot.config import Config


async def make_add_admin_markup(call: CallbackQuery, i18n: I18nMiddleware):
    await call.answer()
    await call.message.edit_text(
        text=(
            'Перешліть повідомлення нижче тому користувачу, '
            'якого хочете додати як оператора'
        ),
        reply_markup=inline.markup_after_creating_link(i18n)
    )
    apply_uuid: uuid.UUID = await db.add_operator_confirm_uuid()
    await call.message.answer(
        text=(
            f'{call.from_user.full_name} хоче додати вас як оператора'
        ),
        reply_markup=inline.apply_operator_markup(
            deep_link=await get_start_link(apply_uuid),
        )
    )

async def add_new_operator(message: Message, config: Config):
    uuid_ = message.get_args()
    await db.delete_operator_confirm_uuid(uuid_)
    await db.add_operator(
        telegram_id=message.from_user.id,
        full_name=message.from_user.full_name,
    )
    await message.answer(
        text=f'Вітаю, {message.from_user.full_name}! Ви тепер оператор',
    )
    # if message.from_user.id in config.tg_bot.admin_ids:
    #     await message.bot.set_my_commands(
    #         commands=[
    #             BotCommand(command="/send", description=messages.send_command),
    #             BotCommand(command='/menu', description=messages.menu_command),
    #             BotCommand(command='/favorites', description=messages.favorites_command),
    #         ],
    #         scope=BotCommandScope(chat_id=message.from_user.id, type='chat')
    #     )
    # else:
    #     await message.bot.set_my_commands(
    #         commands=[
    #             BotCommand(command='/favorites', description=messages.favorites_command),
    #         ],
    #         scope=BotCommandScope(chat_id=message.from_user.id, type='chat')
    #     )

def register_add_operator_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        callback=make_add_admin_markup,
        text='add_operator',
    )
    dp.register_message_handler(
        callback=add_new_operator,
        commands=['start'],
        is_operator_deep_link=True,
        is_operator=False,
    )