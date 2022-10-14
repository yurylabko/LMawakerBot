from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from ..types import ALL_MSGRS

bt_start_reg = InlineKeyboardButton("Да", callback_data="start_reg")
bt_cancel_reg = InlineKeyboardButton("Нет", callback_data="cancel_reg")


kb_strat_reg = InlineKeyboardMarkup().add(bt_start_reg, bt_cancel_reg)

kb_msgr = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(msgr, callback_data=msgr) for msgr in ALL_MSGRS if msgr != "Telegram"],
        [
            InlineKeyboardButton("Отправить", callback_data="msgr_send"),
        ],
    ]
)


def get_kb_end_reg(chat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        row_width=2,
        inline_keyboard=[
            [
                InlineKeyboardButton("Редактировать", callback_data=f"edit_reg{chat_id}"),
                InlineKeyboardButton("Удалить", callback_data=f"reset_reg{chat_id}"),
            ]
        ],
    )
