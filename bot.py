import asyncio
import logging

from lmawakerbot.config import load_config
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.redis import RedisStorage2

from lmawakerbot.handlers.echo import register_echo
from lmawakerbot.handlers.wakeup import register_wakeUp

logger = logging.getLogger()


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s",
    )
    logger.info("Bot started!!!")

    config = load_config()

    bot = Bot(token=config.tg_bot.token, parse_mode="HTML")
    storange = RedisStorage2() if config.use_redis else MemoryStorage()
    dp = Dispatcher(bot=bot, storage=storange)

    register_wakeUp(dp)
    register_echo(dp)

    try:
        await dp.start_polling()
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot stopped!!!")
