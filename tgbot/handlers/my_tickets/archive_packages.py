import io
from aiogram.dispatcher import Dispatcher
from aiogram.types import CallbackQuery
from aiogram import types
from aiogram.contrib.middlewares.i18n import I18nMiddleware

from tgbot.keyboards import inline
from tgbot.services import db
from tgbot.misc import schemas
from tgbot.services.ticket_generator import TicketGenerator


async def show_package(
    call: CallbackQuery,
    callback_data: dict,
    ticket_generator: TicketGenerator,
    i18n: I18nMiddleware,
):
    page_index = int(callback_data.get('page_index'))
    packages: list[schemas.Package] = await db.get_user_archive_packages(
        call.from_user.id,
    )
    if not packages:
        await call.answer(
            text=i18n.gettext('У вас немає посилок в архіві'),
            show_alert=True,
        )
        return
    await call.answer()
    package: schemas.Package = packages[page_index]
    package_image_bytes = await ticket_generator.generate_package(package)
    markup = inline.archive_package_markup(page_index, len(packages))
    args = (call, package_image_bytes, package, markup, i18n)
    if not call.message.photo:
        await send_new_and_delete_old_message(*args)
    else:
        await edit_existing_message(*args)
 

async def edit_existing_message(
    call: CallbackQuery,
    package_image_bytes: bytes,
    package: schemas.Package,
    markup: types.InlineKeyboardMarkup,
    i18n: I18nMiddleware,
):
    await call.message.edit_media(
        media=types.InputMediaPhoto(
            media=types.input_file.InputFile(
                path_or_bytesio=io.BytesIO(package_image_bytes),
            ),
            caption=i18n.gettext(
                '🎫 <b>Ваші посилки з архіву</b> 🎫\n'
                '-------------------------------------------\n'
            ),
        ),
        reply_markup=markup,   
    )


async def send_new_and_delete_old_message(
    call: CallbackQuery,
    package_image_bytes: bytes,
    package: schemas.Package,
    markup: types.InlineKeyboardMarkup,
    i18n: I18nMiddleware,
):
    await call.message.delete()
    await call.message.answer_photo(
        photo=types.input_file.InputFile(
            path_or_bytesio=io.BytesIO(package_image_bytes),
        ),
        caption=i18n.gettext(
            '🎫 <b>Ваші посилки з архіву</b> 🎫\n'
            '-------------------------------------------\n'
        ),
        reply_markup=markup,
    )

            
def register_archive_packages_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        show_package,
        inline.archive_package_navigation_callback.filter(),
    )