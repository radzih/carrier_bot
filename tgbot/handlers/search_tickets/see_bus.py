import re
import logging

from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.types.input_file import InputFile
from aiogram.types import MediaGroup, InputMediaPhoto
from aiogram.contrib.middlewares.i18n import I18nMiddleware
from aiogram.dispatcher.filters import RegexpCommandsFilter

from tgbot.services import db
from tgbot.keyboards import inline


async def show_bus(
    message: Message,
    i18n: I18nMiddleware,
    regexp_command: re.Match,
    state: FSMContext,
):
    await state.finish()
    bus_code = regexp_command.group(1)
    bus = await db.get_bus(bus_code, message.from_user)
    bus_photo = bus.photos[0]
    await message.answer_photo(
        photo=InputFile(bus_photo),
        caption=i18n.gettext(
            '🚌 Автобус: <b>{name}</b>\n'
            'Опис автобуса: {description}\n'
            '{seats} місць\n'
            '{options}\n',
        ).format(
            name=bus.name,
            description=bus.description,
            seats=bus.seats,
            options=', '.join(o.name for o in bus.options),
        ),
        reply_markup=inline.bus_photos_inline_markup(
            all=len(bus.photos),
            photo_index=0,
            bus_code=bus_code,
        ),
    )


async def show_bus_photos(
    call: CallbackQuery,
    i18n: I18nMiddleware,
    callback_data: dict,
):
    await call.answer()
    bus_code = callback_data['bus_code']
    photo_index = int(callback_data['photo_index'])
    bus = await db.get_bus(bus_code, call.from_user)

    await call.message.edit_media(
        media=InputMediaPhoto(
            media=InputFile(bus.photos[photo_index%len(bus.photos)]),
            caption=i18n.gettext(
                '🚌 Автобус: <b>{name}</b>\n'
                'Опис автобуса: {description}\n'
                '{seats} місць\n'
                '{options}\n',
            ).format(
                name=bus.name,
                description=bus.description,
                seats=bus.seats,
                options=', '.join(o.name for o in bus.options),
        ),
 
        ),
        reply_markup=inline.bus_photos_inline_markup(
            bus_code, photo_index, len(bus.photos),
        ),
    )



def register_see_bus_handlers(dp: Dispatcher):
    dp.register_message_handler(
        show_bus,
        RegexpCommandsFilter(
            regexp_commands=[
                '/b_(\w{16})',
            ]
        ),
        state='*',
    )
    dp.register_callback_query_handler(
        show_bus_photos,
        inline.bus_photo_navigation_callback.filter(),
    )