from aiogram.bot import Bot
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.utils import markdown
from aiogram.contrib.middlewares.i18n import I18nMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from tgbot.config import Config
from tgbot.keyboards import inline, reply
from tgbot.handlers import menu
from tgbot.misc import schemas
from tgbot.services import db
from web.app.models import SupportRequest


async def cancel_operator_request(
    call: CallbackQuery,
    i18n: I18nMiddleware,
    state: FSMContext,
    scheduler: AsyncIOScheduler,
    callback_data: dict[str, str],
):
    await call.answer()
    try:
        await db.delete_support_request(int(callback_data['id']))
    except SupportRequest.DoesNotExist:
        pass 
    await menu.show_menu_handler(call, scheduler, state, i18n)


async def support_handler(message: CallbackQuery, i18n: I18nMiddleware):
    await message.answer()
    support_request: schemas.SupportRequest = await db.add_support_request(
        user_telegram_id=message.from_user.id,
    )
    await message.message.edit_text(
        text=i18n.gettext('Зачекайте, шукаю вільного оператора'),
        reply_markup=inline.cancel_operator_request_markup(i18n, support_request.id),
    )
    await send_request_to_operators(
        bot=message.bot,
        text=(
            'Новий запит на підтримку від '
            f'{markdown.hbold(message.from_user.full_name)} '
            'з ID: '
            f'{markdown.hcode(message.from_user.id)} \n'
            f'ID Запиту: {markdown.hcode(support_request.id)} \n'
        ),
        support_request=support_request,
    )

async def send_request_to_operators(
    bot: Bot,
    text: str,
    support_request: schemas.SupportRequest
    ):
    operators: list[schemas.Operator] = await db.get_operators()
    for operator in operators:
        await bot.send_message(
            chat_id=operator.telegram_id,
            text=text,
            reply_markup=inline.confirm_support_request_markup(
                support_request_id=support_request.id,
            ),    
        )

async def confirm_support_request_handler(
    call: CallbackQuery,
    callback_data: dict[str, str],
    state: FSMContext,
    dp: Dispatcher,
    i18n: I18nMiddleware,
    ):
    support_request = await get_support_requests(callback_data)
    await call.answer()
    await call.message.edit_text(
        text=call.message.text + '\nПрийнято',
    )
    await db.delete_support_request(int(callback_data['id']))
    quick_answers = await db.get_quick_answers()
    user: schemas.TelegramUser = await db.get_telegram_user(support_request.user_id)
    # inviter - хто запитував підтримку
    # invitee - хто підтвердив запит
    await set_state_to_support_dialog(
        dp=dp,
        inviter_telegram_id=support_request.user_id,
        invitee_telegram_id=call.from_user.id,
    )
    await call.bot.send_message(
        chat_id=support_request.user_id,
        text=i18n.gettext('Ваш запит прийнято', locale=user.language.code),
        reply_markup=reply.stop_support_dialog_kb(i18n, user.language.code),
    )
    await call.bot.send_message(
        chat_id=call.from_user.id,
        text=(
            'Діалог з користувачем почався. '
        ),
        reply_markup=reply.stop_support_dialog_operator_kb(quick_answers),
    )

async def set_state_to_support_dialog(
    dp: Dispatcher, 
    inviter_telegram_id: int,
    invitee_telegram_id: int,
    ):
    inviter_state = dp.current_state(
        user=inviter_telegram_id,
        chat=inviter_telegram_id,
    )
    await inviter_state.set_state('support_dialog')
    await inviter_state.update_data(
        invitee_telegram_id=invitee_telegram_id,
        inviter_telegram_id=inviter_telegram_id,
    )
    invitee_state = dp.current_state(
        user=invitee_telegram_id,
        chat=invitee_telegram_id,
    )
    await invitee_state.set_state('support_dialog')
    await invitee_state.update_data(
        inviter_telegram_id=inviter_telegram_id,
        invitee_telegram_id=invitee_telegram_id,
    )
 
async def forward_messages(message: Message, state: FSMContext):
    state_data = await state.get_data()
    if message.from_user.id == state_data['inviter_telegram_id']:
        companion_id = state_data['invitee_telegram_id']
    else:
        companion_id = state_data['inviter_telegram_id']
    await message.copy_to(chat_id=companion_id)


async def get_support_requests(callback_data: dict) -> schemas.SupportRequest:
    support_request_id = int(callback_data['id'])
    support_request: schemas.SupportRequest = await db.get_support_request(
        id=support_request_id,
    )
    return support_request

async def stop_dialog_state_between_inviter_and_invitee(
    dp: Dispatcher,
    invitee_telegram_id: int,
    inviter_telegram_id: int,
    ):
    for telegram_id in (invitee_telegram_id, inviter_telegram_id):
        state = dp.current_state(
            user=telegram_id,
            chat=telegram_id,
        )
        await state.reset_state()

async def stop_support_dialog_handler(
    message: Message,
    dp: Dispatcher,
    state: FSMContext,
    i18n: I18nMiddleware,
    ):
    state_data = await state.get_data()
    await stop_dialog_state_between_inviter_and_invitee(
        dp=dp,
        invitee_telegram_id=state_data['invitee_telegram_id'],
        inviter_telegram_id=state_data['inviter_telegram_id'],
    )
    user: schemas.TelegramUser = await db.get_telegram_user(state_data['inviter_telegram_id'])
    if message.from_user.id == state_data['inviter_telegram_id']:
        text_to_user = i18n.gettext('Ви завершили діалог з оператором', locale=user.language.code)
        text_to_support = 'Користувач завершив діалог з оператором'

    else:
        text_to_support = 'Ви завершили діалог з користувачем'
        text_to_user = i18n.gettext('Оператор завершив діалог з вами', locale=user.language.code)
    await (await message.bot.send_message(
        state_data['invitee_telegram_id'],'d',reply_markup=reply.remove_kb)).delete()
    await (await message.bot.send_message(
        state_data['inviter_telegram_id'],'d',reply_markup=reply.remove_kb)).delete()
    await message.bot.send_message(
        chat_id=state_data['invitee_telegram_id'],
        text=text_to_support,
        # reply_markup=inline.add_to_favorite_markup(state_data['inviter_telegram_id']),
    )
    await message.bot.send_message(
        chat_id=state_data['inviter_telegram_id'],
        text=text_to_user,
    )

async def start_dialog_from_operator_to_user(
    call: CallbackQuery,
    dp: Dispatcher,
    callback_data: dict[str, str],
    ):
    await call.answer()
    await call.message.edit_text(
        text=call.message.text + '\nПрийнято',
    )
    await set_state_to_support_dialog(
        dp=dp,
        invitee_telegram_id=int(callback_data['telegram_id']),
        inviter_telegram_id=call.from_user.id,
    )
    await call.bot.send_message(
        chat_id=int(callback_data['telegram_id']),
        text='Діалог з оператором почався',
        reply_markup=reply.stop_support_dialog_kb,
    )
    await call.bot.send_message(
        chat_id=call.from_user.id,
        text=(
            'Діалог з користувачем почався. '
        ),
        reply_markup=reply.stop_support_dialog_kb,
    )
def register_support_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        support_handler,
        text='request_operator',
    )
    dp.register_callback_query_handler(
        confirm_support_request_handler,
        inline.confirm_support_request_callback.filter(),
        state='*',
    )
    dp.register_message_handler(
        stop_support_dialog_handler,
        lambda m: m.text in ['❗️Зупинити діалог❗️', '❗️Остановить диалог❗'],
        state='support_dialog',
    )
    dp.register_message_handler(
        forward_messages,
        state='support_dialog',
        content_types=ContentType.ANY,
    )
    # dp.register_callback_query_handler(
    #     start_dialog_from_operator_to_user,
    #     inline.start_dialog_callback.filter(),
    # )
    dp.register_callback_query_handler(
        cancel_operator_request,
        inline.cancel_operator_request_callback.filter(),
    )