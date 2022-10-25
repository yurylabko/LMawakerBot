import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..pgsql import PGDatabase


def update_database(db: "PGDatabase"):

    db.execute(
        "create table if not exists version(num int4 PRIMARY KEY, description varchar, "
        "created_at timestamp DEFAULT current_timestamp, updated_at varchar);",
        commit=True,
    )

    (db_version,) = db.execute("select max(num) as num from version", fetchone=True)
    logging.info(f"Start DB version = {db_version}")

    try:
        # db.execute("BEGIN")
        if not db_version:
            db.execute(
                "create table if not exists chats(id int primary key, name varchar unique, is_active bool, "
                "created_at timestamp, updated_at timestamp);",
                no_close=True,
            )

            db.execute(
                "create table if not exists users(chat_id int, id int, name varchar, alias varchar, phone_number varchar, messengers varchar, "
                "is_active bool, created_at timestamp, updated_at timestamp, primary key(chat_id, id, name));",
                no_close=True,
            )

            db_version = 1
            db_description = "first init"
            db.execute("insert into version(num, description) values(%s, %s)", params=(db_version, db_description), no_close=True)
            logging.info(f"Update DB schema: #{db_version} done!")

        if db_version <= 1:
            db.execute("alter table chats alter COLUMN id type bigint;", no_close=True)
            db.execute("alter table users alter COLUMN chat_id type bigint;", no_close=True)
            db.execute("alter table users alter COLUMN id type bigint;", no_close=True)
            db_version = 2
            db_description = "change ids type"
            db.execute("insert into version(num, description) values(%s, %s)", params=(db_version, db_description), no_close=True)
            logging.info(f"Update DB schema: #{db_version} done!")

        else:
            logging.info("Update DB schema: no update required")
    except Exception as ex:
        logging.critical(f"Update DB schema error: {ex}")
        db.connection.rollback()
    else:
        db.connection.commit()
        logging.info(f"Current DB version = {db_version}")
