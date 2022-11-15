import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram import types
from aioredis import ConnectionPool
from aiogram.types import BotCommand
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.job import Job
from apscheduler_di import ContextSchedulerDecorator

from tgbot.misc.setup_django import setup_django; setup_django()
from tgbot.filters.admin import AdminFilter
from tgbot.config import load_config, Config
from tgbot.filters.operator import OperatorFilter
from tgbot.filters.user_phone import UserPhoneFilter
from tgbot.handlers.menu import register_menu_handlers
from tgbot.handlers.start import register_start_handlers
from tgbot.handlers.system import register_system_handlers
from tgbot.handlers.errors import register_error_handlers
from tgbot.handlers.settings import register_settings_handlers
from tgbot.handlers.my_tickets import register_my_tickets_handlers
from tgbot.filters.is_registered import IsRegisteredFilter
from tgbot.filters.inline_query_to_send import InlineQueryToSend
from tgbot.middlewares.redis import RedisMiddleware
from tgbot.filters.operator_deep_link import OperatorDeepLink
from tgbot.middlewares.environment import EnvironmentMiddleware
from tgbot.services.ticket_generator import TicketGenerator
from tgbot.filters.state_exclude import StatesExcludeFilter
from tgbot.middlewares.locale import LocaleMiddleware
from tgbot.handlers.share_bot import register_share_bot_handlers
from tgbot.handlers.send_package import register_send_package_handlers
from tgbot.handlers.search_tickets import register_search_tickets_handlers
from tgbot.handlers.request_operator import register_request_operator_handlers


logger = logging.getLogger(__name__)


def register_all_middlewares(
    dp: Dispatcher, 
    config: Config,
    storage: RedisStorage2 | MemoryStorage,
    scheduler: AsyncIOScheduler,
    i18n: LocaleMiddleware,
    ticket_generator: TicketGenerator,
    redis_connection_pool: ConnectionPool,
    ):
    dp.setup_middleware(
        EnvironmentMiddleware(
            config=config,
            dp=dp,
            storage=storage,
            scheduler=scheduler,
            i18n=i18n,
            ticket_generator=ticket_generator,
        )
    )
    dp.setup_middleware(
        RedisMiddleware(
            connection_pool=redis_connection_pool,
        ) 
    )
    dp.setup_middleware(
        LocaleMiddleware(
            domain=config.locale.domain,
        )
    )

def register_all_filters(dp: Dispatcher):
    dp.filters_factory.bind(AdminFilter)
    dp.filters_factory.bind(IsRegisteredFilter)
    dp.filters_factory.bind(UserPhoneFilter)
    dp.filters_factory.bind(OperatorDeepLink)
    dp.filters_factory.bind(OperatorFilter)
    dp.filters_factory.bind(InlineQueryToSend)
    dp.filters_factory.bind(StatesExcludeFilter)



def register_all_handlers(dp: Dispatcher):
    register_menu_handlers(dp)
    register_start_handlers(dp)
    register_share_bot_handlers(dp)
    register_request_operator_handlers(dp)
    register_error_handlers(dp)
    register_search_tickets_handlers(dp)
    register_send_package_handlers(dp)
    register_my_tickets_handlers(dp)
    register_system_handlers(dp)
    register_settings_handlers(dp)

async def set_commands_to_bot(bot: Bot):
    await bot.set_my_commands(
        list(
            BotCommand(command=command, description=description) \
                for command, description in bot['config'].tg_bot.commands.items()
        ),
    )

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
    )
    logger.info("Starting bot")
    config = load_config(".env")

    
    job_stores = {
        "default": RedisJobStore(
            host=config.redis.host,
            jobs_key="dispatched_trips_jobs",
            run_times_key="dispatched_trips_running"
        )
    }    


    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    storage = RedisStorage2() if config.tg_bot.use_redis else MemoryStorage()
    dp = Dispatcher(bot, storage=storage)
    redis_connection_pool = ConnectionPool.from_url(config.redis.url)
    i18n = LocaleMiddleware(config.locale.domain, config.locale.dir)
    ticket_generator = TicketGenerator()
    scheduler = ContextSchedulerDecorator(AsyncIOScheduler(jobstores=job_stores))


    scheduler.ctx.add_instance(instance=bot, declared_class=Bot)
    scheduler.ctx.add_instance(instance=dp, declared_class=Dispatcher)

    bot['config'] = config
    bot['i18n'] = i18n

    register_all_middlewares(
        dp, config, storage, scheduler,i18n, 
        ticket_generator, redis_connection_pool,
    )
    register_all_filters(dp)
    register_all_handlers(dp)


    # dp.register_message_handler(show)

    # start
    try:
        scheduler.start()
        # for job in scheduler.get_jobs():
        #     logging.info(job)
        #     job: Job
        #     job.reschedule(trigger='date', run_date=datetime.now())
        await dp.start_polling()
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()
        await bot.session.close()

# async def show(message):
#     await message.answer(
#         text='sadf',
#         reply_markup=types.InlineKeyboardMarkup(
#             inline_keyboard=[
#                 [
#                     types.InlineKeyboardButton(
#                         text='sadf',
#                         web_app=types.web_app_info.WebAppInfo(
#                             url='https://poki.com/en/g/four-in-a-row'
#                         )
#                     )
#                 ]
#             ]
#         )
#     )

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot stopped!")
