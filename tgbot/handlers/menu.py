import datetime

from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.contrib.middlewares.i18n import I18nMiddleware
from aiogram.types import CallbackQuery
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.base import JobLookupError
from apscheduler.job import Job

from tgbot.keyboards import inline
from tgbot.config import Config


async def show_menu_handler(
    call: CallbackQuery,
    scheduler: AsyncIOScheduler,
    state: FSMContext,
    i18n: I18nMiddleware,
    ):
    await state.finish()
    try: 
        scheduler.remove_job(f'check_package_registration_{call.from_user.id}')
    except JobLookupError:
        pass
    try:
        scheduler.remove_job(f'say_that_ticket_reservation_was_deleted_{call.from_user.id}')
    except JobLookupError:
        pass
    try: 
        job: Job = scheduler.get_job('delete_ticket_reservation_{}'.format(call.from_user.id))
        if job:
            job.modify(next_run_time=datetime.datetime.now())
    except JobLookupError:
        pass
    await state.finish()
    if call.message.photo:
        await call.message.delete()
        answer = call.message.answer
    else:
        answer = call.message.edit_text
    config: Config = call.bot.get("config")
    if call.from_user.id in config.tg_bot.admin_ids:
        markup = inline.menu_admin_markup(i18n),
    else:
        markup = inline.menu_markup(i18n),
    await answer(
        text=i18n.gettext(
            'З поверненням, {}!\n'
            'Ви в <b>головному меню</b>.\n'
        ).format(call.from_user.full_name),
        reply_markup=markup[0]
    )

def register_menu_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        show_menu_handler,
        text='main_menu',
        state='*',
    )