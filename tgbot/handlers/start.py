from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.types import Message, ContentType
from aiogram.contrib.middlewares.i18n import I18nMiddleware

from tgbot.services import db
from tgbot.keyboards import inline, reply
from tgbot.config import Config

start_message_via_bot = {}

async def start_handler_for_not_registered(
    message: Message,
    i18n: I18nMiddleware,
):
    await message.delete()
    sended_message = await message.answer(
        text=i18n.gettext(
            'Для користування ботом, поділіться вашим '
            'номером телефону, натиснувши кнопку нижче.'
        ),
        reply_markup=reply.get_phone_kb(i18n),
    )
    start_message_via_bot[message.from_user.id] = sended_message.message_id

def phone_validation(phone: str) -> str:
    return f'+380{phone[-9:]}'

async def get_user_phone_and_add_to_db(
    message: Message,
    i18n: I18nMiddleware,
):
    await message.delete()
    await message.bot.delete_message(
        chat_id=message.from_user.id,
        message_id=start_message_via_bot[message.from_user.id],
    )
    await (await message.answer('.', reply_markup=reply.remove_kb)).delete()
    validated_phone = phone_validation(message.contact.phone_number)
    await message.answer(
        text=i18n.gettext(
            'Привіт, {}!\n'
            'В цьому боті, Ви зможете <b>замовити автобусні '
            'квитки</b> або <b>відправити посилку</b>, нашою компанією.' 
        ).format(message.from_user.full_name),
        reply_markup=inline.menu_markup(i18n),
    )
    await db.add_telegram_user(
        telegram_id=message.from_user.id,
        full_name=message.from_user.full_name,
        phone=validated_phone,
    )

    
async def start_handler_for_registered(
    message: Message,
    i18n: I18nMiddleware,
    state: FSMContext,
    config: Config,
):
    await message.delete()
    await state.finish()
    if message.from_user.id in config.tg_bot.admin_ids:
        markup = inline.menu_admin_markup(i18n),
    else:
        markup = inline.menu_markup(i18n),
    await message.answer(
        text=i18n.gettext(
            'З поверненням, {}!\n'
            'Ви в <b>головному меню</b>.\n'
        ).format(message.from_user.full_name),
        reply_markup=markup[0],
    )

def register_start_handlers(dp: Dispatcher):
    dp.register_message_handler(
        start_handler_for_not_registered,
        commands=['start'],
        is_registered=False,
    )
    dp.register_message_handler(
        get_user_phone_and_add_to_db,
        is_user_phone=True,
        content_types=ContentType.CONTACT,
    )
    dp.register_message_handler(
        start_handler_for_registered,
        commands=['start'],
        is_registered=True,
        state='*',
    )