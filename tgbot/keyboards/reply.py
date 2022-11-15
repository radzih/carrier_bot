import logging

from aiogram.types.reply_keyboard import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types.reply_keyboard import ReplyKeyboardRemove
from aiogram.contrib.middlewares.i18n import I18nMiddleware

from tgbot.misc import schemas


def get_phone_kb(
    i18n: I18nMiddleware,
) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=i18n.gettext('📞 Поділитися номером 📞'),
                    request_contact=True,
                )
            ]
        ],
        resize_keyboard=True
    )

remove_kb = ReplyKeyboardRemove()

stop_support_dialog_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text='❗️Зупинити діалог❗️',
            )
        ]
    ],
    resize_keyboard=True
)


def route_dates_markup(
    routes: list[schemas.Route],
) -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    j = 0
    dates = list(set(r.user_departure_time.strftime('%d.%m') for r in routes))
    while len(dates) >= j:
        markup.row(
            *set(
                KeyboardButton(
                    text=date,
                ) for date in dates[j:j+2]
            )
        )
        j += 2
    return markup

