from aiogram.dispatcher import Dispatcher

from .start import register_start_handlers
from .language import register_language_handlers
from .notifications import register_notifications_handlers
from .menu import register_menu_handlers


def register_settings_handlers(dp: Dispatcher):
    register_start_handlers(dp)
    register_language_handlers(dp)
    register_notifications_handlers(dp)
    register_menu_handlers(dp)