import asyncio

from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.types import CallbackQuery
from aiogram.utils.exceptions import CantInitiateConversation, BotBlocked
from tgbot.config import Config

from tgbot.keyboards import inline
from tgbot.misc import schemas
from tgbot.services import db


async def request_call_handler(call: CallbackQuery):
    await call.answer()
    await call.message.edit_text(
        text=(
            'Натисніть кнопку <i>"замовити дзвінок"</i>.'
        ),
        reply_markup=inline.request_call_markup,
    )   

async def send_request(call: CallbackQuery, dp: Dispatcher, config: Config):
    user: schemas.TelegramUser = await db.get_telegram_user(call.from_user.id)
    await call.message.edit_text(
        text=(
            '<i>Наш менеджер зв\'яжеться з Вами найближчим часом.</i>\n\n'
            'Якщо Ви ще, не бачили на що здатні боти,'
            'можете переглянути нашу презентацію '
            'натиснувши відповідну кнопку.'
        ),
        reply_markup=inline.after_request_markup,
    )
    await send_request_call_to_operators(
        bot=call.bot,
        dp=dp,
        user_telegram_id=user.telegram_id,
    )

async def send_request_call_to_operators(
    bot: Bot,
    dp: Dispatcher,
    user_telegram_id: int
):
    operators: list[schemas.Operator] = await db.get_operators()
    user: schemas.TelegramUser = await db.get_telegram_user(user_telegram_id)
    while operators:
        operator = operators.pop()
        operator_state = dp.current_state(
            user=operator.telegram_id,
            chat=operator.telegram_id,
            )
        if await operator_state.get_state() is not None:
            operators.append(operator)
            await asyncio.sleep(0.5)
            continue
        try:
            await bot.send_message(
                chat_id=operator.telegram_id,
                text=(
                    'Запит на зворотній зв\'язок:\n'
                    f'<b>Ім\'я:</b> {user.full_name}\n'
                    f'<b>Номер телефону:</b> {user.phone}\n'
                ),
            )
        except (CantInitiateConversation, BotBlocked):
            continue
    
    

def register_request_call_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        request_call_handler,
        is_user_have_phone=True,
        text='request_call',
    )
    dp.register_callback_query_handler(
        send_request,
        text='send_request',
    )