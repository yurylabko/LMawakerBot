from aiogram import types, Dispatcher
from aiogram.utils.markdown import hcode


async def bot_wakeUp(message: types.Message):
    player_name = message.get_args()
    answer = [
        f"Сбора на {hcode(player_name)}?",
    ]

    await message.reply("\n".join(answer))


def register_wakeUp(dp: Dispatcher):
    dp.register_message_handler(bot_wakeUp, commands=["wakeUp"])
