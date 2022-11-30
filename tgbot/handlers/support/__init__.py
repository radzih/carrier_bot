from aiogram.dispatcher import Dispatcher

from . import support, operators_menu, add_operator, manage_operators


def register_support_handlers(dp: Dispatcher):
    support.register_support_handlers(dp)
    operators_menu.register_operators_menu_handlers(dp)
    add_operator.register_add_operator_handlers(dp)
    manage_operators.register_manage_operators_handlers(dp)