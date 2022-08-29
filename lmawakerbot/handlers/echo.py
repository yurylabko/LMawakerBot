from aiogram import types, Dispatcher
from aiogram.utils.markdown import hcode


async def bot_echo(message: types.Message):
    answer = [
        "Сообщение без состояния",
        "Текст сообщения:",
        hcode(message.text),
    ]

    await message.reply("\n".join(answer))


def register_echo(dp: Dispatcher):
    dp.register_message_handler(bot_echo)
