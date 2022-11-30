from aiogram.dispatcher import Dispatcher
from aiogram.types import CallbackQuery, BotCommand, BotCommandScope
from aiogram.contrib.middlewares.i18n import I18nMiddleware
from tgbot.config import Config

from tgbot.services import db
from tgbot.keyboards import inline
from tgbot.misc import schemas


async def see_all_operators(
    call: CallbackQuery,
    callback_data: dict,
    i18n: I18nMiddleware,
):
    await call.answer()
    page = int(callback_data.get('page', 0))
    markup = await create_markup_for_view_operators(page, i18n)
    await call.message.edit_text(
        text=(
            'Нижче ви бачите список операторів\n\n'
            'Натиснувши на оператора ви зможете '
            'переглянути інформацію про нього або видалити '
        ),
        reply_markup=markup
    )

async def create_markup_for_view_operators(page: int, i18n: I18nMiddleware):
    operators: list[schemas.Operator] = await db.get_operators()
    markup = inline.page_navigation_for_operators_markup(operators, page, i18n)
    return markup

async def view_info_about_operator(
    call: CallbackQuery,
    callback_data: dict,
    i18n: I18nMiddleware,
):
    await call.answer()
    operator_telegram_id = int(callback_data.get('telegram_id'))
    operator: schemas.Operator = await db.get_operator(id=operator_telegram_id)
    await call.message.edit_text(
        text=(
            'Оператор\n\n'
            f'Ім\'я: {operator.full_name}\n'
            f'ID телеграм: {operator.telegram_id}\n\n'
        ),
        reply_markup=inline.delete_operator_markup(operator.telegram_id, i18n)
    )
    
async def delete_operator(
    call: CallbackQuery,
    callback_data: dict,
    config: Config,
    ):
    await call.answer()
    operator_telegram_id = int(callback_data.get('telegram_id'))
    operator: schemas.Operator = await db.delete_operator(
        id=operator_telegram_id
        )
    await call.message.edit_text(
        text=(
            f'Оператора {operator.full_name} видалено'
        ),
    )
    # if operator_telegram_id in config.tg_bot.admin_ids:
    #     await call.bot.set_my_commands(
    #         commands=[
    #             BotCommand(command="/send", description=messages.send_command),
    #             BotCommand(command='/menu', description=messages.menu_command),
    #         ],
    #         scope=BotCommandScope(chat_id=call.from_user.id, type='chat')
    #     )
    # else:
    #     await call.bot.set_my_commands(
    #         commands=[
    #             BotCommand(command='/start', description=messages.start_command),
    #         ],
    #         scope=BotCommandScope(chat_id=operator_telegram_id, type='chat')
    #     )

def register_manage_operators_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        see_all_operators,
        inline.operator_navigation_callback.filter(),
    )
    dp.register_callback_query_handler(
        delete_operator,
        inline.delete_operator_callback.filter(),
    )
    dp.register_callback_query_handler(
        view_info_about_operator,
        inline.operator_callback.filter()
    )
