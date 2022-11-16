from aiogram.contrib.middlewares.i18n import I18nMiddleware
from aiogram import types
from aiogram.utils.callback_data import CallbackData
from aiogram.types.inline_keyboard import InlineKeyboardMarkup, \
    InlineKeyboardButton

from tgbot.misc import schemas


go_to_menu_cross_button = InlineKeyboardButton(
    text='❎',
    callback_data='main_menu',
)


go_to_menu_cross_button_markup = \
    InlineKeyboardMarkup().add(go_to_menu_cross_button)


cancel_operator_request_markup = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text='⭕️ Відмінити ⭕️',
                callback_data='cancel_operator_request',
            )
        ]
    ]
)

def search_tickets_button(i18n: I18nMiddleware) -> InlineKeyboardButton:
    return  InlineKeyboardButton(
        text=i18n.gettext('🔎 Пошук квитків 🔎'),
        callback_data='search_tickets',
    ) 

    
def send_package_button(i18n: I18nMiddleware) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=i18n.gettext('📦 Відправити посилку 📦'),
        callback_data='send_package',
    )

def search_tickets_markup(i18n: I18nMiddleware) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                search_tickets_button(i18n)
            ]
        ]
    )
 

def menu_markup(i18n: I18nMiddleware) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                search_tickets_button(i18n),
            ],
            [
                send_package_button(i18n),
            ],
            [
                InlineKeyboardButton(
                    text=i18n.gettext('🎫 Мої квитки/посилки 🎫'),
                    callback_data='my_tickets',
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.gettext('⚙ Налаштування ⚙'),
                    callback_data='settings',
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.gettext('🙋‍♂️ Підключити оператора 🙋'),
                    callback_data='request_operator',
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.gettext('↖️ Поділитися ботом ↗️'),
                    switch_inline_query='share_bot',
                )
            ]
        ]
    )


def got_to_bot_markup(bot_username: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Перейти до бота',
                    url=f'https://t.me/{bot_username}',
                )
            ]
        ]
    )


request_call_markup = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text='📲 Замовити дзвінок 📲',
                callback_data='send_request',
            )
        ],
        [
            go_to_menu_cross_button
        ]
    ]
)

after_request_markup = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            go_to_menu_cross_button
        ]
    ]
)


accept_operator_request_callback = CallbackData(
    'accept_operator_request', 'id'
)


def accept_operator_request_markup(request_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='✅ Підключитися ✅',
                    callback_data=accept_operator_request_callback.new(
                        id=request_id,
                    )
                )
            ]
        ]
    )


no_operators_markup = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text='📞 Передзвоніть мені  📞',
                callback_data='request_call_after_no_operators',
            )
        ],
        [
            InlineKeyboardButton(
                text='👌🏻 Я почекаю 👌🏻',
                callback_data='wait_for_operator',
            )
        ]
    ]
)

wait_for_operator_markup = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text='📞 Передзвоніть мені  📞',
                callback_data='request_call_after_no_operators',
            )
        ],
        [
            InlineKeyboardButton(
                text='⭕️ Відмінити ⭕️',
                callback_data='cancel_operator_request',
            )
        ]
    ]
)


tickets_navigation_callback = CallbackData('tickets_navigation', 'page_index')
def my_tickets_menu(
    i18n: I18nMiddleware,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.gettext('🎫 Переглянути квитки 🎫'),
                    callback_data=tickets_navigation_callback.new(
                        page_index=0,
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=i18n.gettext('📦 Переглянути посилки 📦'),
                    callback_data=package_navigation_callback.new(
                        page_index=0,
                    )
                ),
            ],
            [
                InlineKeyboardButton(
                    text=i18n.gettext('🗂 Архів 🗂 '),
                    callback_data='archive' 
                ),
            ],
            [
                go_to_menu_cross_button,
            ]
        ]
    )
    

def add_navigation_buttons(
    markup: InlineKeyboardMarkup, 
    page: int, 
    column_lenth: int, 
    total_pages: int,
    callback_data: CallbackData,
    ) -> InlineKeyboardMarkup:
    markup.row(
        InlineKeyboardButton(
            text='<',
            callback_data=callback_data.new(
                page_index=(page - 1) % total_pages,    
            ),
        ),
        InlineKeyboardButton(
            text=f'{page+1}/{total_pages}',
            callback_data='...', 
        ),
        InlineKeyboardButton(
            text='>',
            callback_data=callback_data.new(
                page_index=(page + 1) % total_pages,
            )
        )
    )
    return markup


return_ticket_callback = CallbackData('return_ticket', 'ticket_id', 'is_paid')
def ticket_markup(
    ticket: schemas.Ticket,
    page_index: int,
    ticket_amount: int,
    i18n: I18nMiddleware,
) -> InlineKeyboardMarkup: 
    URL = 'https://maps.google.com/?q={latitude},{longitude}'
    markup = InlineKeyboardMarkup()
    add_navigation_buttons(
        markup,
        page=page_index,
        column_lenth=1,
        total_pages=ticket_amount,
        callback_data=tickets_navigation_callback,
    )
    markup.add(
        InlineKeyboardButton(
            text=i18n.gettext('❌ Повернути квиток ❌'),
            callback_data=return_ticket_callback.new(
                ticket_id=ticket.id,
                is_paid=ticket.is_paid,
            ),
        )
    )
    markup.add(
        InlineKeyboardButton(
            text=i18n.gettext('🗺 Станція відправлення 🗺'),
            url=URL.format(
                latitude=ticket.start_station.latitude,
                longitude=ticket.start_station.longitude,
            )
        )
    )
    markup.row(
        InlineKeyboardButton(
            text='🔙',
            callback_data='my_tickets',
        ),
        go_to_menu_cross_button,
    )
    return markup

def after_ticket_refund_markup(
    i18n: I18nMiddleware,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                search_tickets_button(i18n),
            ],
            [
                InlineKeyboardButton(
                    text='🔙',
                    callback_data=tickets_navigation_callback.new(
                        page_index=0,
                    ),
                ),
                go_to_menu_cross_button,
            ]
        ]
    )


return_package_callback = CallbackData('return_package', 'package_id', 'is_paid')
package_navigation_callback = CallbackData('package_navigation', 'page_index')
def package_markup(
    package: schemas.Package,
    page_index: int,
    packages_amount: int,
    i18n: I18nMiddleware,
) -> InlineKeyboardMarkup: 
    markup = InlineKeyboardMarkup()
    URL = 'https://maps.google.com/?q={latitude},{longitude}'
    add_navigation_buttons(
        markup,
        page=page_index,
        column_lenth=1,
        total_pages=packages_amount,
        callback_data=package_navigation_callback,
    )
    markup.add(
        InlineKeyboardButton(
            text=i18n.gettext('❌ Скасувати відправку ❌'),
            callback_data=return_package_callback.new(
                package_id=package.id,
                is_paid=package.is_paid,
            ),
        )
    )
    markup.add(
        InlineKeyboardButton(
            text=i18n.gettext('🗺 Станція відправлення 🗺'),
            url=URL.format(
                latitude=package.start_station.latitude,
                longitude=package.start_station.longitude,
            )
        )
    )
    markup.row(
        InlineKeyboardButton(
            text='🔙',
            callback_data='my_tickets',
        ),
        go_to_menu_cross_button,
    )
    return markup

def after_package_refund_markup(
    i18n: I18nMiddleware,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                send_package_button(i18n),
            ],
            [
                InlineKeyboardButton(
                    text='🔙',
                    callback_data=package_navigation_callback.new(
                        page_index=0,
                    ),
                ),
                go_to_menu_cross_button,
            ]
        ]
    )


def archive_markup(
    i18n: I18nMiddleware,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.gettext('📦Мої посилки'),
                    callback_data=archive_package_navigation_callback.new(
                        page_index=0,
                    )
                ),
            ],
            [
                InlineKeyboardButton(
                    text=i18n.gettext('🎫 Мої квитки'),
                    callback_data=archive_ticket_navigation_callback.new(
                        page_index=0,
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    text='🔙',
                    callback_data='my_tickets',
                ),
                go_to_menu_cross_button,
            ]
        ]
    )
    


archive_ticket_navigation_callback = CallbackData(
    'archive_ticket_navigation',
    'page_index',
)
def archive_ticket_markup(
    page_index: int,
    ticket_amount: int,
) -> InlineKeyboardMarkup: 
    markup = InlineKeyboardMarkup()
    add_navigation_buttons(
        markup,
        page=page_index,
        column_lenth=1,
        total_pages=ticket_amount,
        callback_data=archive_ticket_navigation_callback
    )
    markup.row(
        InlineKeyboardButton(
            text='🔙',
            callback_data='archive',
        ),
        go_to_menu_cross_button,
    )
    return markup

archive_package_navigation_callback = CallbackData(
    'archive_package_navigation',
    'page_index',
)
def archive_package_markup(
    page_index: int,
    ticket_amount: int,
) -> InlineKeyboardMarkup: 
    markup = InlineKeyboardMarkup()
    add_navigation_buttons(
        markup,
        page=page_index,
        column_lenth=1,
        total_pages=ticket_amount,
        callback_data=archive_package_navigation_callback
    )
    markup.row(
        InlineKeyboardButton(
            text='🔙',
            callback_data='archive',
        ),
        go_to_menu_cross_button,
    )
    return markup


def settings_markup(i18n: I18nMiddleware) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.gettext('🌐 Мова 🌐'),
                    callback_data='language',
                ),
            ],
            [
                InlineKeyboardButton(
                    text=i18n.gettext('🔔 Нагадування 🔔'),
                    callback_data='notifications',
                ),
            ],
            [
                go_to_menu_cross_button,
            ]
        ]
    )


set_language_callback = CallbackData('set_language', 'language_id')
def languages_markup(languages: list[schemas.Language]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=language.name,
                    callback_data=set_language_callback.new(
                        language_id=language.id,
                    ),
                )
            ]
            for language in languages
        ]
    ).row(
        InlineKeyboardButton(
            text='🔙',
            callback_data='settings',
        ),
        go_to_menu_cross_button
        )

    
def turn_notifications_markup(
    i18n: I18nMiddleware,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.gettext('Ввімкнути/вимкнути'),
                    callback_data='turn_notifications',
                ),
            ],
            [
                InlineKeyboardButton(
                    text='🔙',
                    callback_data='settings',
                ),
                go_to_menu_cross_button,
            ]
        ]
    )


station_callback = CallbackData('station', 'station_id')
def user_station_history_markup(
    stations: list[schemas.Station],
) -> InlineKeyboardMarkup:
    keyboard = []
    j = 0
    for i in stations:
        if j % 2 == 0:
            keyboard.append([])
        keyboard[-1].append(
            InlineKeyboardButton(
                text=i.full_name,
                callback_data=station_callback.new(
                    station_id=i.id,
                ),
            )
        )
        j += 1

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )

def cancel_button(i18n: I18nMiddleware):
    return InlineKeyboardButton(
        text='✖️ скасувати',
        callback_data='cancel'
    )

close_markup = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text='✖️',
                callback_data='cancel',
            )
        ]
    ]
)


def finded_stations_markup(
    i18n: I18nMiddleware,
    stations: list[schemas.Station],
): 
    markup = InlineKeyboardMarkup()
    j = 0
    while len(stations) >= j:
        markup.row(
            *list(
                InlineKeyboardButton(
                    text=station.full_name,
                    callback_data=station_callback.new(
                        station_id=station.id,
                    )
                ) for station in stations[j:j+2]
            )
        )
        j += 2
    markup.add(cancel_button(i18n))
    return markup
        

ticket_amount_callback = CallbackData('ticket_amount', 'amount')
def ticket_amount_markup(amount: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i,
                    callback_data=ticket_amount_callback.new(
                        amount=i,
                    )
                )
            for i in range(1, amount+1)
            ]
        ]
    )


ticket_type_callback = CallbackData('ticket_type', 'ticket_type_id')
def ticket_type_markup(
    ticket_types: list[schemas.TicketType],
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=ticket_type.name.capitalize(),
                    callback_data=ticket_type_callback.new(
                        ticket_type_id=ticket_type.id
                    )
                )
            ] for ticket_type in ticket_types
        ]
    )


pay_for_tickets_callback = CallbackData('pay_for_tickets', 'tickets_ids')
def pay_for_tickets_markup(
    i18n: I18nMiddleware,
    tickets_ids: list[int],
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.gettext('💳 Перейти до оплати 💳'),
                    pay=True,
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.gettext('🚌 Оплатити в автобусі 🚌'),
                    callback_data=pay_for_tickets_callback.new(
                        tickets_ids='|'.join(str(id) for id in tickets_ids),
                    ),
                )
            ]
        ]
    )

pay_for_package_callback = CallbackData('pay_for_package', 'redis_key', sep='|')
def pay_for_package_markup(
    i18n: I18nMiddleware,
    redis_key: str,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.gettext('💳 Перейти до оплати 💳'),
                    pay=True,
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.gettext('🚌 Оплатити в автобусі 🚌'),
                    callback_data=pay_for_package_callback.new(
                        redis_key=redis_key,
                    ),
                )
            ]
        ]
    )


def routes_markup(
    i18n: I18nMiddleware,
    end_station_id: int,
    date: str
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.gettext('↪️ Зворотній квиток'),
                    callback_data='change_stations',
                ),
                InlineKeyboardButton(
                    text=i18n.gettext('📆 Інший день'),
                    callback_data=station_callback.new(
                        station_id=end_station_id,
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.gettext('🔄 Оновити дані'),
                    callback_data=f'refresh_routes:{date}',
                ),
                InlineKeyboardButton(
                    text=i18n.gettext('🔍 Новий пошук 🔍'),
                    callback_data='search_tickets'
                )
            ]
        ]
    )

def package_routes_markup(
    i18n: I18nMiddleware,
    end_station_id: int,
    date: str
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.gettext('↪️ Зворотній квиток'),
                    callback_data='package_change_stations',
                ),
                InlineKeyboardButton(
                    text=i18n.gettext('📆 Інший день'),
                    callback_data='package_another_day',
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.gettext('🔄 Оновити дані'),
                    callback_data=f'package_refresh_routes:{date}',
                ),
                InlineKeyboardButton(
                    text=i18n.gettext('🔍 Новий пошук 🔍'),
                    callback_data='send_package'
                )
            ]
        ]
    )

def link_to_start_station(i18n: I18nMiddleware, url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='🗺Станція відправлення',
                    url=url,
                )
            ]
        ]
    )

def popular_stations_markup(
    stations: list[schemas.Station],
    i18n: I18nMiddleware,
) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    j = 0
    while len(stations) >= j:
        markup.row(
            *list(
                InlineKeyboardButton(
                    text=station.full_name,
                    callback_data=station_callback.new(
                        station_id=station.id,
                    )
                ) for station in stations[j:j+2]
            )
        )
        j += 2
    markup.add(search_tickets_button(i18n))
    return markup
 

bus_photo_navigation_callback = CallbackData(
    'bus_photo_navigation', 'bus_code', 'photo_index',
)
def bus_photos_inline_markup(
    bus_code: str,
    photo_index: int,
    all: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='⬅️',
                    callback_data=bus_photo_navigation_callback.new(
                        bus_code=bus_code,
                        photo_index=(photo_index - 1) % all,
                    ),
                ),
                InlineKeyboardButton(
                    text='➡️',
                    callback_data=bus_photo_navigation_callback.new(
                        bus_code=bus_code,
                        photo_index=(photo_index + 1) % all,
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text='✖',
                    callback_data='cancel'
                )
            ]
        ]
    )


def play_game(i18n: I18nMiddleware, game_link, lk) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.gettext('🎮 Грати 🎮', locale=lk),
                    web_app=types.web_app_info.WebAppInfo(
                        url=game_link,
                    )
                )
            ]
        ]
    )