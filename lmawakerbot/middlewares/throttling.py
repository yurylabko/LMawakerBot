import asyncio

from typing import Union
from aiogram.dispatcher import DEFAULT_RATE_LIMIT

# from aiogram.dispatcher import DEFAULT_RATE_LIMIT
from aiogram.dispatcher.middlewares import BaseMiddleware

from aiogram import types, Dispatcher
from aiogram.utils.exceptions import Throttled
from aiogram.dispatcher.handler import current_handler, CancelHandler


class ThrottlingMiddlewares(BaseMiddleware):
    def __init__(self, limit=DEFAULT_RATE_LIMIT, key_prefix="antiflood_"):
        self.limit = limit
        self.prefix = key_prefix
        super(ThrottlingMiddlewares, self).__init__()

    async def throttle(self, target: Union[types.Message, types.CallbackQuery]):
        handler = current_handler.get()
        if not handler:
            return
        dp = Dispatcher.get_current()
        limit = getattr(handler, "throttling_rate_limit", self.limit)
        key = getattr(handler, "throttling_key", f"{self.prefix}_{handler.__name__}")

        try:
            await dp.throttle(key, rate=limit)
        except Throttled as t:
            await self.target_throttled(target, t, dp, key)
            raise CancelHandler()

    @staticmethod
    async def target_throttled(target: Union[types.Message, types.CallbackQuery], throttled: Throttled, dp: Dispatcher, key: str):
        msg = target.message if isinstance(target, types.CallbackQuery) else target
        delta = throttled.rate - throttled.delta
        if throttled.exceeded_count == 2:
            await msg.reply("Слишком часто! АСТАНАВИСЬ!!!!")
            return
        elif throttled.exceeded_count == 3:
            await msg.reply(f"Утомил!!! Не буду отвечать еще {int(delta)} секунд ")
            return
        await asyncio.sleep(delta)

        thr = await dp.check_key(key)
        if thr.exceeded_count == throttled.exceeded_count:
            await msg.reply("Все, теперь буду отвечать!!!")

    async def on_process_message(self, message, data):
        await self.throttle(message)
