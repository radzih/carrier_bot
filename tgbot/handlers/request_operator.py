import asyncio
import datetime

from aiogram import Bot
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.types import Message, CallbackQuery, ContentTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from aiogram.utils.exceptions import CantInitiateConversation, BotBlocked
from aiogram.contrib.middlewares.i18n import I18nMiddleware

from tgbot.keyboards import inline
from tgbot.keyboards import reply
from tgbot.misc import schemas
from tgbot.services import db
from tgbot.handlers.request_call import send_request_call_to_operators
from tgbot.handlers import menu


async def send_request(
    call: CallbackQuery, 
    state: FSMContext,
    dp: Dispatcher,
    scheduler: AsyncIOScheduler,
    ):
    await call.answer()
    await state.set_state('waiting_for_operator')
    message = await call.message.edit_text(
        text=(
            f'{call.from_user.full_name}, наш менеджер вже поспішає в чат...'
        ),
        reply_markup=inline.cancel_operator_request_markup,
    )
    request: schemas.SupportRequest = await db.add_support_request(
        user_telegram_id=call.from_user.id,
        message_id_to_edit=message.message_id,
    )
    await send_request_to_operators(call.bot, dp, request.id)
    scheduler.add_job(
        id=f'request_operator_{call.from_user.id}',
        trigger=DateTrigger(
            run_date=datetime.datetime.now() + datetime.timedelta(seconds=60)
            ),
        func=check_if_dialog_started,
        kwargs={
            'support_request_id': request.id,
            'edit_message_id': message.message_id,
        }
        
    )

async def send_request_to_operators(
    bot: Bot,
    dp: Dispatcher,
    support_request_id: int,
    ):
    operators: list[schemas.Operator] = await db.get_operators()
    support_request: schemas.SupportRequest = await db.get_support_request(support_request_id)
    user: schemas.TelegramUser = await db.get_telegram_user(support_request.user_id)
    while operators: 
        operator = operators.pop()
        operator_state = dp.current_state(
            user=operator.telegram_id, 
            chat=operator.telegram_id,
            )
        if await operator_state.get_state() is not None:
            operators.append(operator)
            await asyncio.sleep(0.2)
            continue
        try: 
            await bot.send_message(
                chat_id=operator.telegram_id,
                text=(
                    f'{user.full_name}, запросив підтримку в чаті'
                ),
                reply_markup=inline.accept_operator_request_markup(
                    request_id=support_request.id,
                    ),
            )
        except (CantInitiateConversation, BotBlocked):
            continue
            

async def check_if_dialog_started(
    bot: Bot, 
    dp: Dispatcher,
    support_request_id: int,
    edit_message_id: int,
    ):
    support_request: schemas.SupportRequest = await db.get_support_request(
        support_request_id
        )
    user_state = dp.current_state(
        user=support_request.user_id, 
        chat=support_request.user_id,
        )
    if await user_state.get_state() != 'waiting_for_operator': return
    await bot.edit_message_text(
        chat_id=support_request.user_id,
        message_id=edit_message_id,
        text=(
            'Наразі маємо невеличке завантаження, '
            'Ви можете ще трошки почекати, або залишити '
            'свої контакти і ми з Вами зв\'яжемось, як тільки '
            'з\'явиться вільний менеджер.'
        ), 
        reply_markup=inline.no_operators_markup,
    )

async def request_call_after_no_operators(
    call: CallbackQuery,
    dp: Dispatcher,
    state: FSMContext,
    ):
    await call.answer()
    await state.finish()
    await call.message.edit_text(
        text=(
            'Зазвичай ми зв\'язуємось з клієнтами в '
            'робочий час з 9:00 до 18:00, до зв\'язку ✋🏻'
        ),
        reply_markup=inline.go_to_menu_markup,
    )
    await send_request_call_to_operators(
        bot=call.bot,
        user_telegram_id=call.from_user.id,
        dp=dp,
        )

async def wait_for_operator(call: CallbackQuery):
    await call.answer()
    await call.message.edit_text(
        text=(
            'Добре, я пришвидшу наших менеджерів...'
        ),
        reply_markup=inline.wait_for_operator_markup,
    )

async def cancel_operator_request(
    call: CallbackQuery, 
    state: FSMContext,
    i18n: I18nMiddleware,
    scheduler: AsyncIOScheduler,
    ):
    await state.finish()
    if scheduler.get_job(f'request_operator_{call.from_user.id}'):
        scheduler.remove_job(f'request_operator_{call.from_user.id}')
    await menu.show_menu_handler(call, scheduler, state, i18n)

async def start_support_conversation(
    call: CallbackQuery,
    callback_data: dict,
    state: FSMContext,
    i18n: I18nMiddleware,
    dp: Dispatcher,
    ):
    await call.answer()
    support_request_id = int(callback_data['id'])
    support_request: schemas.SupportRequest = await db.get_support_request(
        id=support_request_id,
    )
    user: schemas.TelegramUser = await db.get_telegram_user(
        telegram_id=support_request.user_id
        )
    user_state = dp.current_state(
        user=support_request.user_id,
        chat=support_request.user_id,
    )
    if await user_state.get_state() != 'waiting_for_operator': 
        return await call.message.edit_text(
            text=(
                'Клієнт віключився від розмови, '
                'або інший оператор вже відповів.'
            ),
        )
    await call.message.delete()
    await call.message.answer(
        text=(
            f'Ви на зв\'язку з клієнтом, {user.full_name}.'
        ),
        reply_markup=reply.stop_support_dialog_kb,
    )
    await call.bot.delete_message(
        chat_id=support_request.user_id,
        message_id=support_request.message_id_to_edit,
        )
    await call.bot.send_message(
        chat_id=support_request.user_id,
        text=(
            f'Оператор {call.from_user.full_name} підключився до розмови, '
            'можете задати своє питання.'
        ),
        reply_markup=reply.stop_support_dialog_kb,
    )
    await user_state.set_state('support_conversation')
    await user_state.update_data(
        operator_id=call.from_user.id,
        user_id=support_request.user_id, 
    )
    await state.set_state('support_conversation')
    await state.update_data(
        operator_id=call.from_user.id,
        user_id=support_request.user_id, 
    )
    await db.delete_support_request(
        request_id=support_request_id,
    )

async def support_conversation(message: Message, state: FSMContext):
    state_data = await state.get_data()
    if message.from_user.id == state_data['operator_id']:
        await message.copy_to(state_data['user_id'])
    else:
        await message.copy_to(state_data['operator_id'])

async def stop_support_conversation(
    message: Message,
    state: FSMContext,
    dp: Dispatcher,
):
    state_data = await state.get_data()
    if message.from_user.id == state_data['operator_id']:
        await message.bot.send_message(
            chat_id=state_data['user_id'],
            text=(
                f'Оператор {message.from_user.full_name} завершив розмову'
            ),
            reply_markup=reply.remove_kb,
        )
    else:
        await message.bot.send_message(
            chat_id=state_data['operator_id'],
            text=(
                f'Клієнт {message.from_user.full_name} завершив розмову'
            ),
            reply_markup=reply.remove_kb,
        )
    await message.answer(
        text='Розмову завершено',
        reply_markup=reply.remove_kb,
    )
    for user_in in state_data.values():
        user_state = dp.current_state(
            user=user_in,
            chat=user_in,
        )
        await user_state.finish()
    
    

def register_request_operator_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        send_request,
        text='request_operator',
    )
    dp.register_callback_query_handler(
        request_call_after_no_operators,
        text='request_call_after_no_operators',
        state='waiting_for_operator',
    )
    dp.register_callback_query_handler(
        wait_for_operator,
        text='wait_for_operator',
        state='waiting_for_operator',
    )
    dp.register_callback_query_handler(
        cancel_operator_request,
        text='cancel_operator_request',
        state='waiting_for_operator',
    )
    dp.register_callback_query_handler(
        start_support_conversation,
        inline.accept_operator_request_callback.filter(),
    )
    dp.register_message_handler(
        stop_support_conversation,
        text='❗️Зупинити діалог❗️',
        state='support_conversation',
    )
    dp.register_message_handler(
        support_conversation,
        content_types=ContentTypes.ANY,
        state='support_conversation',
    )