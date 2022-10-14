from dataclasses import dataclass, field

import logging
import string
from typing import List
from phonenumbers import PhoneNumber, parse, carrier, geocoder, is_valid_number, NumberParseException
from aiogram.utils.markdown import hlink
from .messengers import ALL_MSGRS


@dataclass
class Phone:

    number: str
    language_code: str = "ru"

    def __str__(self) -> str:
        if phonenumber := self.try_get_valid_phonenumber(self.number):
            return (
                f"{self.number} {carrier.name_for_number(phonenumber, self.language_code)}"
                f" {geocoder.description_for_number(phonenumber, self.language_code)}"
            )
        else:
            return self.number

    @staticmethod
    def try_get_valid_phonenumber(phone: str) -> PhoneNumber:
        try:
            phonenumber = parse(phone, None)
        except NumberParseException as ex:
            logging.error(f"parse error for number '{phone}' ({ex})")
            return None
        else:
            return phonenumber if is_valid_number(phonenumber) else None


@dataclass
class User:
    id: int
    name: str = None
    alias: List[str] = field(default_factory=list)
    phone_number: str = None
    language_code: str = "ru"
    messengers: set = field(default_factory=set)

    def __str__(self) -> str:
        return "\n".join(
            (
                f"Имя: {self.name}",
                f"Дополнительные имена: {','.join(self.alias)}",
                f"Телефон: {Phone(self.phone_number, self.language_code)}",
                f"Мессенджеры: {','.join(self.messengers)}",
            )
        )

    @staticmethod
    def is_valid_name(user_name: str) -> bool:
        if not user_name or len(user_name) > 20 or any(s for s in user_name if s not in string.ascii_letters + " " + string.digits):
            return False
        return True


@dataclass
class Chat:
    id: int
    name: str

    def __str__(self) -> str:
        return f"Группа: {self.name} (id:{self.id})"


@dataclass()
class Registration:

    chat: Chat
    user: User

    def __str__(self) -> str:
        return "\n".join((str(self.chat), str(self.user)))

    def show_contacts(self):
        return "\n".join(
            [
                f"Телефон: {Phone(self.user.phone_number, self.user.language_code)}",
                f"Мессенджеры: {', '.join(hlink(msgr, ALL_MSGRS[msgr](self).get_link()) for msgr in self.user.messengers)}",
            ]
        )

    @classmethod
    def from_dict(cls, data: dict):
        chat = data.get("chat")
        user = data.get("user")
        return cls(
            Chat(chat.get("id"), chat.get("name")),
            User(
                user.get("id"),
                user.get("name"),
                user.get("alias"),
                user.get("phone_number"),
                user.get("language_code"),
                user.get("messengers"),
            ),
        )
