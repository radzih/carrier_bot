from io import BytesIO
from PIL import Image

from aiogram.dispatcher import Dispatcher
from aiogram.contrib.middlewares.i18n import I18nMiddleware
from aiogram.types.input_file import InputFile
from aiogram.types import InlineQuery,\
    InlineQueryResultArticle, InputTextMessageContent

from tgbot.keyboards import inline
from tgbot.integrations.telegraph import TelegraphService


async def share_bot_handler(
    inline_query: InlineQuery,
    i18n: I18nMiddleware,
):
    bot = await inline_query.bot.me

    img = Image.open('data/logo.png')
    uploader = TelegraphService()
    b = BytesIO()
    img.save(b, format='PNG')
    photo_link = await uploader.upload_photo(b.getvalue())
    await uploader.close()

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
            thumb_url=photo_link.link,
            description=(
                'Привіт, я бот який допоможе тобі замовити '
                'автобусні квитки або відправити посилку.\n'
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
