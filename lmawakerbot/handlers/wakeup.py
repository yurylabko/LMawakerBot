import logging
import asyncio
from typing import List
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import ChatTypeFilter
from aiogram.utils.markdown import hbold, hcode

from ..keyboards.wakeUp import get_kb_wakeUp, kb_cancel_waleUp

from ..types.classes import Registration

from ..utils.misc.throttling import rate_limit
from ..utils.db_api.sqlite import Database
from ..states.wakeUp import WakeUp


@rate_limit(5, "wakwUp")
async def bot_wakeUp(message: types.Message):
    chat_id = message.chat.id
    language_code = message.from_user.language_code
    player_name = message.get_args()
    # found_by_name = True
    if not player_name:
        await message.reply("Укажите кого сборят? /wakwUp XXXXXXX, где XXXXXXX - имя игрока")
        return
    db: Database = message.bot.get("db")
    logging.debug(f"Поиск игрока с именем {player_name} в чате {chat_id}")
    regs: List(Registration) = db.search_registration(chat_id, name=player_name, language_code=language_code)
    if not regs:
        logging.debug(f"Поиск игрока с псевдонимом {player_name} в чате {chat_id}")
        regs = db.search_registration(chat_id, alias=player_name, language_code=language_code)
    if not regs:
        logging.debug(f"Поиск по имени {player_name} в чате {chat_id} не дал результатов")
        await message.reply(f"Игрок с именем {hbold(player_name)} не найден")
        return
    if len(regs) == 1:
        answer = f"Сбора на {hbold(regs[0].user.name)}?"
    else:
        answer = "Укажите кого будить?"

    await message.reply(answer, reply_markup=get_kb_wakeUp(regs))


async def try_wakeUp(query: types.CallbackQuery, state: FSMContext):
    chat_id = query.message.chat.id
    user_id = int(query.data.split("|")[1])
    language_code = query.from_user.language_code

    current_state = await state.storage.get_state(user=user_id)
    if current_state == WakeUp.start.state:
        data = await state.storage.get_data(user=user_id)
        user_name = data.get("user_name")
        group_id = data.get("group_id")
        if chat_id == group_id:
            await query.message.edit_text("\n" + hbold("У ") + hcode(user_name) + hbold(" будильник уже работает!"))
            return

    db: Database = query.message.bot["db"]

    if not db.is_exists_user(chat_id, user_id):
        await query.message.edit_text(hbold("\nРегистрация не найдена!"))
        logging.warning(f"Не найдена регистрация пользователя (chat_id:{chat_id}, user_id:{user_id})")
        return

    reg = db.get_registration(chat_id, user_id, language_code)
    await query.message.edit_text(
        "\n" + hbold("Пытаюсь разбудить ") + hcode(reg.user.name) + f"\nЕго контакты:\n{reg.show_contacts()}", disable_web_page_preview=True
    )
    await state.storage.set_state(user=user_id, state=WakeUp.start.state)
    data = await state.storage.get_data(user=user_id)
    data["user_name"] = reg.user.name
    data["group_id"] = chat_id
    await state.storage.set_data(user=user_id, data=data)
    i = 0
    while i < 5:
        await query.bot.send_message(
            user_id,
            f"ВНИМАНИЕ!!!. Тебя очень хотят видеть в группе {reg.chat.name}",
            reply_markup=kb_cancel_waleUp if i < 4 else types.ReplyKeyboardRemove(),
        )
        await asyncio.sleep(30)
        current_state = await state.storage.get_state(user=user_id)
        if current_state == WakeUp.cancel.state:
            await query.bot.send_message(user_id, "Я вас понял!", reply_markup=types.ReplyKeyboardRemove())
            await query.message.edit_text(query.message.text + f"\n{hbold('Есть контакт!')}", disable_web_page_preview=True)
            break
        i += 1
    await state.storage.reset_state(user=user_id, with_data=True)


async def cancel_wakeUp(message: types.Message, state: FSMContext):
    if await state.get_state() == WakeUp.start.state:
        await WakeUp.cancel.set()


def register_wakeUp(dp: Dispatcher):
    dp.register_message_handler(bot_wakeUp, ChatTypeFilter([types.ChatType.SUPERGROUP, types.ChatType.GROUP]), commands=["wakeUp", "up"])
    dp.register_callback_query_handler(try_wakeUp, lambda c: c.data.startswith("wakeUp"))
    dp.register_message_handler(
        cancel_wakeUp, ChatTypeFilter([types.ChatType.PRIVATE]), lambda message: message.text == "❌ Заткнись", state=WakeUp.start
    )
