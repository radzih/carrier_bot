from aiogram.dispatcher import Dispatcher
from aiogram.contrib.middlewares.i18n import I18nMiddleware
from aiogram.types import InlineQuery,\
    InlineQueryResultArticle, InputTextMessageContent

from tgbot.keyboards import inline


async def share_bot_handler(
    inline_query: InlineQuery,
    i18n: I18nMiddleware,
):
    bot = await inline_query.bot.me
    results = [
        InlineQueryResultArticle(
            id='share_bot',
            title=i18n.gettext('Поділитися ботом'),
            input_message_content=InputTextMessageContent(
                message_text=(
                    'Привіт, я бот який допоможе тобі замовити '
                    'автобусні квитки або відправити посилку.\n'
                ),
            ),
            reply_markup=inline.got_to_bot_markup(bot.username),
        ),
    ]
    await inline_query.answer(
        results=results,
    )
    

def register_share_bot_handlers(dp: Dispatcher):
    dp.register_inline_handler(
        share_bot_handler,
        text='share_bot',
    )
