import datetime
import logging
import re

from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram import Bot, types
from aiogram.contrib.middlewares.i18n import I18nMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher.filters.builtin import RegexpCommandsFilter
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aioredis import Redis
from aiogram.utils.exceptions import MessageToDeleteNotFound
from tgbot.config import Config


from tgbot.keyboards import reply, inline
from tgbot.services import db
from tgbot.misc import states, schemas
from tgbot.handlers.search_tickets.payloads import ticket_payment_payload



async def get_passengers(
    message: Message,
    i18n: I18nMiddleware,
    regexp_command: re.Match,
    state: FSMContext,
):
    await message.answer(
        text=i18n.gettext(
            '🔍 Отримую к-ть квитків...'
        )
    )

    ( 
        start_station_code,
        end_station_code,
        route_code,
    ) = regexp_command.groups()

    route = await db.get_route(
        start_station_code,
        end_station_code,
        route_code,
    )

    if route.available_seats // 5:
        show_seats = 5
    else:
        show_seats = route.available_seats

    await message.answer(
        text=i18n.gettext(
            '🎫 Доступно {available_seats} місць.\n'
            'Введіть необхідну кількість квитків, або '
            'оберіть з запропонованої кількості 👇'
        ).format(
            available_seats=route.available_seats,
        ),
        reply_markup=inline.ticket_amount_markup(show_seats),
    )
    await states.SelectTicket.get_passengers_amount.set()
    await state.update_data(
        route=route,
    )


async def get_passengers_amount_message(
    message: Message,
    i18n: I18nMiddleware,
    state: FSMContext,
):
    state_data = await state.get_data()
    if not message.text.isdigit():
        await message.answer(
            text=i18n.gettext(
                '🚫 Ви ввели не число.'
            )
        )
        return
    elif int(message.text) > state_data['route'].available_seats:
        await message.answer(
            text=i18n.gettext(
                '🚫 Ви ввели число більше за кількість доступних місць.'
            )
        )
        return
    elif int(message.text) < 1:
        await message.answer(
            text=i18n.gettext(
                '🚫 Ви ввели число менше за 1.'
            )
        )
        return
    elif int(message.text) > 5:
        await message.answer(
            text=i18n.gettext(
                '🚫 Ви ввели число більше за 5.'
            )
        )
        return
    
    await state.update_data(
        passengers_amount=int(message.text),
        current_passenger=1,
    )

    await message.answer(
        text=i18n.gettext(
            '🔍 Отримую дані...'
        )
    )

    await state.update_data(
        passenger_info={i: {} for i in range(1, int(message.text) + 1)}
        
    )
    await select_ticket_type(message, i18n)


async def get_passenger_amount_callback(
    call: CallbackQuery,
    i18n: I18nMiddleware,
    callback_data: dict,
    state: FSMContext,
):
    await call.message.delete()
    await state.update_data(
        passengers_amount=int(callback_data['amount']),
        current_passenger=1,
    )
    await state.update_data(
        passenger_info={i: {} for i in range(1, int(callback_data['amount']) + 1)}
    )
    call.message.from_user.id = call.from_user.id
    await select_ticket_type(call.message, i18n)
 

    

async def select_ticket_type(
    message: Message,
    i18n: I18nMiddleware,
    current_passenger: int = 1,
):
    await states.SelectTicket.get_passenger_ticket_type.set()

    ticket_types = await db.get_ticket_types(message.from_user.id)


    make_ticket_type_markup = inline.ticket_type_markup(ticket_types)
    await message.answer(
        text=i18n.gettext(
            'Оберіть тип для квитка {} 👇'
        ).format(current_passenger),
        reply_markup=make_ticket_type_markup,
    )


async def get_passenger_ticket_type(
    call: CallbackQuery,
    i18n: I18nMiddleware,
    state: FSMContext,
    callback_data: dict,
):
    await call.answer()
    state_data = await state.get_data()

    passenger_info = state_data['passenger_info']
    passenger_info[state_data['current_passenger']]['ticket_type_id'] = int(callback_data['ticket_type_id'])
    
    await state.update_data(
        passenger_info=passenger_info,
    )
    await call.message.edit_text(
        text=i18n.gettext(
            '💺 Кому бронюємо квиток {current_passenger}?\n\n'
            '✍️ Напишіть Ім\'я та Прізвище.\n'
            'Наприклад: Тарас Шевченко'
        ).format(current_passenger=state_data['current_passenger']),
    )
    await states.SelectTicket.get_passenger_full_name.set()


async def get_passenger_full_name(
    message: Message,
    i18n: I18nMiddleware,
    state: FSMContext,
    config: Config,
    scheduler: AsyncIOScheduler,
    redis: Redis,
):
    state_data = await state.get_data()
    if len(message.text.split()) != 2:
        await message.answer(
            text=i18n.gettext(
                '🚫 Ви ввели не повне ім\'я.'
            )
        )
        return

    passenger_info = state_data['passenger_info']
    passenger_info[state_data['current_passenger']]['full_name'] = message.text
        
    await state.update_data(
        passenger_info=passenger_info,
    )

    await state.update_data(
        current_passenger=state_data['current_passenger']+1,
    )

    state_data = await state.get_data()


    if state_data['current_passenger'] <= state_data['passengers_amount']:
        return await select_ticket_type(message, i18n, state_data['current_passenger'])
    await state.finish()
    
    await message.answer(
        text=i18n.gettext(
        'Ок, бронюю місця 🙌\n'
        'Дайте мені декілька секунд...'
        )
    )

    persons = []
    for id, passenger in state_data['passenger_info'].items():
        persons.append(
            schemas.Person(
                id=id,
                name=passenger['full_name'].split()[0].strip(),
                surname=passenger['full_name'].split()[1].strip(),
                phone=None
            )
        )
    

    booked_tickets = []
    for person in persons:
        ticket: schemas.Ticket = await db.book_ticket(
            route_id=state_data['route'].id,
            start_station_id=state_data['route'].user_start_station.id,
            end_station_id=state_data['route'].user_end_station.id,
            telegram_id=message.from_user.id,
            passenger=person,
            type_id=state_data['passenger_info'][person.id]['ticket_type_id'],
        )
        booked_tickets.append(ticket)

    text = generate_payment_message(booked_tickets, i18n)

    await message.answer(
        text=text,
    )

    payment_message = await message.bot.send_invoice(
        chat_id=message.from_user.id,
        title='Покупка квитків',
        description='Покупка квитків',
        provider_token=config.tg_bot.payments_provider_token,
        currency='UAH',
        prices=[
            types.LabeledPrice(
                label=i18n.gettext('Покупка квитків'),
                amount=sum(ticket.price for ticket in booked_tickets)*100,
            ),
        ],
        payload=ticket_payment_payload.new(
            tickets_ids='|'.join(str(ticket.id) for ticket in booked_tickets),
        ),
        reply_markup=inline.pay_for_tickets_markup(
            i18n, [ticket.id for ticket in booked_tickets]
        )
    )
    await redis.set(
        f'payment_message:{message.from_user.id}',
        payment_message.message_id
    )
    await redis.set(
        f'ticket_payment_message_id:{message.from_user.id}',
        payment_message.message_id,
    )

    scheduler.add_job(
        edit_payment_message,
        trigger='date',
        run_date=datetime.datetime.now() + datetime.timedelta(minutes=10),
        kwargs={
            'user_id': message.from_user.id,
            'payment_message_id': payment_message.message_id,
        }
    )
    

async def edit_payment_message(
    bot: Bot,
    user_id: int,
    payment_message_id: int,
):
    if not payment_message_id:
        return
    user = await db.get_telegram_user(user_id)
    i18n: I18nMiddleware = bot.get('i18n')
    try:
        await bot.delete_message(
            chat_id=user_id,
            message_id=payment_message_id,
        )
        await bot.send_message(
            chat_id=user_id,
            text=i18n.gettext(
                '🚫 Платіж був скасований.',
                locale=user.language.code,
            ),
        )
    except MessageToDeleteNotFound:
        pass
    


def generate_payment_message(
    booked_tickets: list[schemas.Ticket],
    i18n: I18nMiddleware,
):
    messages = [
        i18n.gettext(
            '<b><i>Якщо замовлення вірне, перейдіть до оплати.</i></b>\n'
            '<i>(для оплати у вас є 10 хв)</i>\n\n'
            '〰️〰️〰️〰️〰️〰️〰️〰️\n'
        )
    ]
    for index, ticket in enumerate(booked_tickets):
        messages.append(
            i18n.gettext(
                '📝Ваше замовлення📝\n'
                '🎫 Квиток {index}\n'
                '🚌↗️ Відправлення:  {start_station}\n'
                '🚌↙️ Прибуття:  {end_station}\n'
                '🗓 Дата та час відправлення: {date}\n'
                '👥 ПІБ пасажира:\n'
                '{full_name}\n'
                '🎟 Тип квитка: {ticket_type}\n'
                '💸 ціна: {price} грн\n\n'
                '〰️〰️〰️〰️〰️〰️〰️〰️\n'
            ).format(
                index=index+1,
                start_station=ticket.start_station.full_name,
                end_station=ticket.end_station.full_name,
                date=ticket.departure_time.strftime('%d.%m.%Y %H:%M'),
                full_name=f'{ticket.passenger.surname} {ticket.passenger.name}',
                ticket_type=ticket.type.name,
                price=ticket.price,
            )
        )
    return ''.join(messages)


def register_get_passengers_handlers(dp: Dispatcher):
    dp.register_message_handler(
        get_passengers,
        RegexpCommandsFilter(
            regexp_commands=[
                r'/bt_(\w{4})(\w{4})(\w{6})',
            ]
        )
    )
    dp.register_message_handler(
        get_passengers_amount_message,
        state=states.SelectTicket.get_passengers_amount,
    )
    dp.register_callback_query_handler(
        get_passenger_ticket_type, 
        inline.ticket_type_callback.filter(),
        state=states.SelectTicket.get_passenger_ticket_type,
    )
    dp.register_message_handler(
        get_passenger_full_name,
        state=states.SelectTicket.get_passenger_full_name,
    )
    dp.register_callback_query_handler(
        get_passenger_amount_callback,
        inline.ticket_amount_callback.filter(),
        state=states.SelectTicket.get_passengers_amount,
    )
