from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from ..types.classes import Registration


def get_kb_wakeUp(regs: List[Registration]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        row_width=2,
        inline_keyboard=[[InlineKeyboardButton(f"Будить {reg.user.name}", callback_data=f"wakeUp|{reg.user.id}") for reg in regs]],
    )


kb_cancel_waleUp = ReplyKeyboardMarkup(
    [
        [
            KeyboardButton("❌ Заткнись"),
        ]
    ],
    one_time_keyboard=True,
    resize_keyboard=True,
)
