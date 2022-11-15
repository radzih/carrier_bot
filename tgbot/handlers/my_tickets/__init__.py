from aiogram.dispatcher import Dispatcher

from .main import register_main_handlers
from .ticket_view import register_ticket_view_handlers
from .package_view import register_package_view_handlers
from .return_ticket import register_return_ticket_handlers
from .return_package import register_return_package_handlers
from .archive import register_archive_handlers
from .archive_tickets import register_archive_tickets_handlers
from .archive_packages import register_archive_packages_handlers


def register_my_tickets_handlers(dp: Dispatcher):
    register_main_handlers(dp)
    register_ticket_view_handlers(dp)
    register_package_view_handlers(dp)
    register_return_ticket_handlers(dp)
    register_return_package_handlers(dp)
    register_archive_handlers(dp)
    register_archive_tickets_handlers(dp)
    register_archive_packages_handlers(dp)
