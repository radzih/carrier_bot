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

def stop_support_dialog_kb(i18n, locale):
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=i18n.gettext('❗️Зупинити діалог❗️', locale=locale),
                )
            ]
        ],
        resize_keyboard=True
    )

def stop_support_dialog_operator_kb(
    quick_answers: list[schemas.QuickAnswer]
) -> ReplyKeyboardMarkup:
    markup =  ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text='❗️Зупинити діалог❗️',
                )
            ],
        ],
        resize_keyboard=True
    )
    
    [
        markup.add(
            KeyboardButton(
                text=ans.text,
            )
        ) for ans in quick_answers
    ]
    
    return markup



def route_dates_markup(
    routes: list[schemas.Route],
) -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    j = 0
    dates = list(set(r.user_departure_time for r in routes))
    dates = sorted(dates)
    while len(dates) >= j:
        markup.row(
            *list(
                reversed(
                    [KeyboardButton(
                        text=date.strftime("%d.%m"),
                    ) for date in dates[j:j+2]
                    ]
                )
            )
        )
        j += 2
    return markup

