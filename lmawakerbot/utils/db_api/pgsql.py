from functools import partial
import psycopg2

# import logging
from typing import List, Tuple
from psycopg2 import extras

from ...types.classes import Chat, Registration
from .migration.pgsql import update_database


class PGDatabase:
    def __init__(self, URL: str = "main.db") -> None:
        self.__url = URL
        self.__connection = None

        update_database(self)

    @property
    def connection(self):
        if not self.__connection or self.__connection.closed:
            self.__connection = psycopg2.connect(self.__url, sslmode="prefer")
        return self.__connection

    def execute(
        self,
        sql: str,
        params: Tuple = None,
        commit: bool = False,
        fetchall: bool = False,
        fetchone: bool = False,
        is_Row: bool = False,
        no_close: bool = False,
    ) -> list:
        if not params:
            params = ()

        connection = self.connection

        # connection.set_trace_callback(lambda s: logging.info(f"Executing: {s}"))
        cursor = connection.cursor()
        if is_Row:
            cursor = connection.cursor(cursor_factory=extras.DictCursor)

        data = None

        cursor.execute(sql, params)

        if commit:
            connection.commit()
        elif fetchall:
            data = cursor.fetchall()
        elif fetchone:
            data = cursor.fetchone()

        if not no_close:
            connection.close()
        return data

    def add_or_update_chat(self, chat: Chat):
        sql_add = """
        insert into chats(id, name, is_active, created_at) VALUES(%s, %s, %s, CURRENT_TIMESTAMP)
        """
        sql_update = """
        update chats set name = %s, is_active = %s,  updated_at = CURRENT_TIMESTAMP where id = %s
        """

        if self.is_exists_chat(chat.id):
            self.execute(
                sql_update,
                (
                    chat.name,
                    True,
                    chat.id,
                ),
                commit=True,
            )
        else:
            self.execute(
                sql_add,
                (
                    chat.id,
                    chat.name,
                    True,
                ),
                commit=True,
            )

    def add_or_update_user(self, reg: Registration):
        sql_add = """
        insert into users(chat_id, id, name, alias, phone_number, messengers, is_active, created_at)
        VALUES(%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        """
        sql_update = """
        update users set name = %s, alias = %s, phone_number = %s, messengers = %s, is_active = %s,
        updated_at = CURRENT_TIMESTAMP where chat_id = %s and id = %s
        """

        if self.is_exists_user(reg.chat.id, reg.user.id):
            self.execute(
                sql_update,
                (
                    reg.user.name,
                    ",".join(reg.user.alias),
                    reg.user.phone_number,
                    ",".join(reg.user.messengers),
                    True,
                    reg.chat.id,
                    reg.user.id,
                ),
                commit=True,
            )
        else:
            self.execute(
                sql_add,
                (
                    reg.chat.id,
                    reg.user.id,
                    reg.user.name,
                    ",".join(reg.user.alias),
                    reg.user.phone_number,
                    ",".join(reg.user.messengers),
                    True,
                ),
                commit=True,
            )

    def is_exists_user(self, chat_id: int, user_id: int):
        sql = """
        select 1 from users where chat_id = %s and id = %s
        """
        return self.execute(
            sql,
            (
                chat_id,
                user_id,
            ),
            fetchone=True,
        )

    def is_exists_name(self, chat_id: int, user_name: str):
        sql = """
        select 1 from users where chat_id = %s and user_name = %s
        """
        return self.execute(
            sql,
            (
                chat_id,
                user_name,
            ),
            fetchone=True,
        )

    def is_exists_chat(self, chat_id: int):
        sql = """
        select 1 from chats where id = %s
        """
        return self.execute(sql, (chat_id,), fetchone=True)

    def select_all_users(self, chat_id: int):
        sql = """
        SELECT * FROM Users where chat_uid = %s
        """
        return self.execute(sql, (chat_id,), fetchall=True)

    def reset_registration(self, chat_id: int, user_id: int):
        sql = [
            """delete from users where chat_id = %s and id = %s;""",
        ]
        exec = partial(
            self.execute,
            params=(
                chat_id,
                user_id,
            ),
            commit=True,
        )
        list(map(exec, sql))

    def show_registrations(self, user_id: int) -> List[Chat]:
        sql = """
        SELECT id, name FROM Chats where id in (select chat_id from Users where id = %s)
        """
        res = self.execute(sql, (user_id,), fetchall=True)

        return [Chat(*r) for r in res]

    def get_chat(self, chat_id: int) -> Chat:
        sql = """
        SELECT id, name FROM Chats where id = %s
        """
        res = self.execute(sql, (chat_id,), fetchone=True)

        return Chat(*res)

    def get_registration(self, chat_id: int, user_id: int, language_code: str) -> Registration:
        sql = """
        SELECT c.id as chat_id, c.name as chat_name, u.id as user_id, u.name as user_name, u.alias, u.phone_number, u.messengers
          FROM chats c inner join users u on c.id = u.chat_id
         where c.id = %s and u.id = %s
        """
        res = self.execute(
            sql,
            (
                chat_id,
                user_id,
            ),
            fetchone=True,
            is_Row=True,
        )
        chat = {"id": res["chat_id"], "name": res["chat_name"]}
        user = {
            "id": res["user_id"],
            "name": res["user_name"],
            "alias": res["alias"].split(","),
            "phone_number": res["phone_number"],
            "language_code": language_code,
            "messengers": set(res["messengers"].split(",")),
        }
        return Registration.from_dict({"chat": chat, "user": user})

    def search_registration(self, chat_id: int, name: str = None, alias: str = None, language_code: str = "ru"):
        sql_name = """
        SELECT c.id as chat_id, c.name as chat_name, u.id as user_id, u.name as user_name, u.alias, u.phone_number, u.messengers
          FROM chats c inner join users u on c.id = u.chat_id
         where c.id = %s and u.name = %s
        """
        sql_alias = """
        SELECT c.id as chat_id, c.name as chat_name, u.id as user_id, u.name as user_name, u.alias, u.phone_number, u.messengers
          FROM chats c inner join users u on c.id = u.chat_id
         where c.id = %s and u.alias || ',' || u.name ilike %s
         ESCAPE '='
        """
        if name:
            rows = self.execute(
                sql_name,
                (
                    chat_id,
                    name,
                ),
                fetchall=True,
                is_Row=True,
            )
        else:
            alias = alias.replace("=", "==").replace("%", "=%").replace("_", "=_")
            rows = self.execute(
                sql_alias,
                (
                    chat_id,
                    "%" + alias + "%",
                ),
                fetchall=True,
                is_Row=True,
            )
        ret = []
        for res in rows:
            chat = {"id": res["chat_id"], "name": res["chat_name"]}
            user = {
                "id": res["user_id"],
                "name": res["user_name"],
                "alias": res["alias"].split(","),
                "phone_number": res["phone_number"],
                "language_code": language_code,
                "messengers": set(res["messengers"].split(",")),
            }
            ret.append(Registration.from_dict({"chat": chat, "user": user}))
        return ret
