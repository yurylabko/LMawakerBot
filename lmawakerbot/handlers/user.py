from dataclasses import asdict
import logging

from typing import List

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hcode, hbold
from ..utils.db_api.sqlite import Database
from ..states.registration import StateReg
from ..keyboards.registation import kb_strat_reg, get_kb_end_reg, kb_msgr

# from ..utils.misc.validator import is_valid_name, is_valid_phone
from ..types import Phone, User, Registration, Chat


ANSWER_YES = "да"
ANSWER_NO = "нет"


async def start_user_reg(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    # user_name = message.from_user.full_name
    chat_id = message.chat.id
    chat_title = message.chat.title
    language_code = message.from_user.language_code

    msg_args = message.get_args()

    if chat_id == user_id and not (msg_args or isinstance(msg_args, int)):
        await message.reply("Регистрация доступна только из чата группы")
        return

    db: Database = message.bot.get("db")
    chat = {}
    user = {}
    chat["id"] = chat_id
    chat["name"] = chat_title

    try:
        db.add_or_update_chat(Chat(chat_id, chat_title))
    except Exception as ex:
        logging.critical(f"Ошибка сохранения чата в бд. ({ex})")

    user["id"] = user_id
    user["language_code"] = language_code

    if db.is_exists_user(chat_id, user_id):
        await message.bot.send_message(
            user_id,
            f"Вы уже зарегистрированы в группе {hcode(chat_title)}\n"
            f"Отправьте \n/show для просмотра списка всех регистраций"
            f"\n{'/show' + str(abs(chat_id))} для просмотра регистрации в группе {chat_title}",
        )
        return

    reg = {"chat": chat, "user": user}
    await state.storage.set_data(chat=user_id, user=user_id, data=reg)
    await state.storage.set_state(chat=user_id, user=user_id, state=StateReg.start.state)
    await message.bot.send_message(user_id, f"Хотите зарегистрироваться в группе {chat_title} (id:{chat_id})", reply_markup=kb_strat_reg)


async def reset_regState(message: types.Message, state: FSMContext):
    await state.finish()
    await state.reset_data()
    await message.answer(f"Регистрация прекращена. Для запуска регистрации отправьте команду {hcode('/reg')} из чата группы!")


async def req_user_name(query: types.CallbackQuery | types.Message):
    await StateReg.name.set()
    if isinstance(query, types.CallbackQuery):
        await query.message.edit_text("Введите имя:")
    else:
        await query.answer("Введите имя:")


async def set_user_name(message: types.Message, state: FSMContext):
    user_name = message.text
    if not User.is_valid_name(user_name):
        await message.answer("Вы ввели некорректное имя, попробуйте еще раз.")
        await req_user_name(message)
        return
    data = await state.get_data()
    data["user"]["name"] = user_name
    await state.update_data(data)
    await req_user_alias(message=message)


async def req_user_alias(message: types.Message):
    await StateReg.alias.set()
    await message.answer("Введите дополнительное имя, можно несколько (списком через запятую):")


async def set_user_alias(message: types.Message, state: FSMContext):
    msg_data = message.text
    alias = msg_data.split(",")

    invalid_user_names = [n for n in alias if not User.is_valid_name(n)]

    if invalid_user_names and alias:
        await message.answer(f"Вы ввели некорректные имена: {','.join(invalid_user_names)}, попробуйте еще раз")
        await req_user_alias(message=message)
        return
    data = await state.get_data()
    data["user"]["alias"] = alias
    await state.update_data(data)
    await req_user_phone(message)


async def req_user_phone(message: types.Message):
    await StateReg.phone.set()
    await message.answer("Введите номер телефона в международном формате:")


async def set_user_phone(message: types.Message, state: FSMContext):
    phone_numner = message.text

    if phone_numner and not Phone.try_get_valid_phonenumber(phone_numner):
        await message.answer("Вы ввели некорректный номер телефона, попробуйте еще раз.")
        await req_user_phone(message)
        return
    data = await state.get_data()
    data["user"]["phone_number"] = phone_numner
    await state.update_data(data)
    await req_user_messengers(message, state)


async def req_user_messengers(message: types.Message, state: FSMContext):
    await StateReg.messenger.set()
    data = await state.get_data()
    data["user"]["messengers"] = set(
        [
            "Telegram",
        ]
    )
    await state.update_data(data)
    await message.answer("Выберите мессенджеры для связи", reply_markup=kb_msgr)


async def edit_user_messengers(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    messengers: set = (data.get("user")).get("messengers")
    query_text = "Выберите мессенджеры для связи:"
    messenger = query.data
    if messenger == "msgr_send":
        await query.message.edit_text(query_text + "\nВы выбрали: " + (", ".join(messengers)))
        await req_confirm_registration(query.message, state)
        return
    if messenger in messengers:
        messengers.remove(messenger)
    else:
        messengers.add(messenger)
    data["user"]["messengers"] = messengers
    await state.update_data(data)
    await query.message.edit_text(query_text + "\nВы выбрали: " + (", ".join(messengers)), reply_markup=kb_msgr)


async def req_confirm_registration(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.finish()
    reg = Registration.from_dict(data)
    try:
        save_registration(message.bot.get("db"), reg)
    except Exception as ex:
        logging.error(f"Ошибка сохранения регистрации в бд: ({ex})")
    else:
        await message.answer("Регистрация прошла успешно!\nВы ввели следующие данные:")
        await show_registration(message, reg)


def save_registration(db: Database, reg: Registration):
    db.add_or_update_chat(reg.chat)
    db.add_or_update_user(reg)


async def show_registration(message: types.Message, reg: Registration) -> None:

    await message.answer(
        text=str(reg),
        reply_markup=get_kb_end_reg(reg.chat.id),
    )


async def show_registrations(message: types.Message):
    user_id = message.from_user.id
    db: Database = message.bot.get("db")
    chats: List[Chat] = db.show_registrations(user_id)
    if not chats:
        await message.reply("Регистрации отсутсвуют. Попробуйте зарегистрироваться из чата группы.")
    else:
        await message.answer("Список всех регистраций:\n" + "\n".join(f"{chat.name} {'/show' + str(abs(chat.id))}" for chat in chats))


async def show_registration_detail(message: types.Message):
    user_id = message.from_user.id
    language_code = message.from_user.language_code
    try:
        chat_id = -1 * int(message.text[5:])
    except Exception as ex:
        logging.error(f"Ошибка парчинга id чата: ({ex})")
        await message.reply("Чат не определен")
        return
    db: Database = message.bot.get("db")
    reg: Registration = db.get_registration(chat_id, user_id, language_code)
    await show_registration(message, reg)


async def reset_user_reg(query: types.CallbackQuery):
    user_id = query.from_user.id
    chat_id = int(query.data[9:])

    db: Database = query.message.bot["db"]
    if not db.is_exists_user(chat_id, user_id):
        await query.message.edit_text(query.message.text + hbold("\nРегистрация не найдена!"))
    else:
        try:
            db.reset_registration(chat_id, user_id)
        except Exception as ex:
            await query.message.edit_text(query.message.text + hbold("\nПроизошла ошибка при удалении регистрации!"))
            logging.warn(f"Ошибка удаления регистрации пользователя {(chat_id, user_id)}: {ex.args}")
        await query.message.edit_text(query.message.text + hbold("\nРегистрация удалена!"))


async def edit_user_reg(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    chat_id = int(query.data[8:])
    language_code = query.from_user.language_code
    db: Database = query.bot.get("db")
    reg: Registration = db.get_registration(chat_id, user_id, language_code)

    await state.update_data(asdict(reg))
    await req_user_name(query.message)


async def alter_button(callback_query: types.CallbackQuery, state: FSMContext):
    bot = callback_query.bot
    await bot.answer_callback_query(callback_query_id=callback_query.id, text="В данный момент кнопка неактивна", show_alert=True)


def register_user(dp: Dispatcher):

    dp.register_message_handler(show_registration_detail, lambda message: message.text.startswith("/show") and len(message.text) > 5)
    dp.register_message_handler(show_registrations, commands=["show"])
    dp.register_message_handler(start_user_reg, commands=["reg", "start"])
    dp.register_message_handler(reset_user_reg, commands=["reset"])
    # dp.register_message_handler(set_user_name, Text(equals=ANSWER_YES, ignore_case=True), state=StateReg.start)
    dp.register_callback_query_handler(req_user_name, lambda c: c.data == "start_reg", state=StateReg.start)
    dp.register_callback_query_handler(reset_user_reg, lambda c: c.data.startswith("reset_reg"))
    dp.register_callback_query_handler(edit_user_reg, lambda c: c.data.startswith("edit_reg"))
    # dp.register_message_handler(reset_regState, Text(equals=ANSWER_NO, ignore_case=True), state=StateReg.start)
    dp.register_message_handler(set_user_name, state=StateReg.name)
    dp.register_message_handler(set_user_alias, state=StateReg.alias)
    dp.register_message_handler(set_user_phone, state=StateReg.phone)
    dp.register_callback_query_handler(edit_user_messengers, state=StateReg.messenger)
    dp.register_callback_query_handler(alter_button, state="*")
    # dp.register_callback_query_handler(alter_start, lambda c: c.data == "start_reg")
    # dp.register_callback_query_handler(alert_cancel, lambda c: c.data == "cancel_reg")
