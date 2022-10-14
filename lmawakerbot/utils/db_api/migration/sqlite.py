import logging

from ..sqlite import Database


def update_database(db: Database):

    (db_version,) = db.execute("PRAGMA user_version;", fetchone=True)
    logging.info(f"Start DB version = {db_version}")

    try:
        db.execute("BEGIN")
        if not db_version:
            db.execute("create table if not exists chats(id int primary key, name text unique, is_active int, created_at int, updated_at int);")

            db.execute(
                "create table if not exists users(chat_id int, id int, name text, alias text, phone_number text, messengers text, "
                "is_active int, created_at int, updated_at int, primary key(chat_id, id, name));"
            )

            db_version = 1
            logging.info(f"Update DB schema: #{db_version} done!")

        # if db_version <= 1:
        #     db.execute(
        #         "create table if not exists link_user2chat(user_id int not null, chat_id int primary key, "
        #         "is_active int, create_at int, update_at int);"
        #     )
        #     db_version = 2
        #     logging.info(f"Update DB schema: #{db_version} done!")
        else:
            logging.info("Update DB schema: no update required")
    except Exception as ex:
        logging.critical(f"Update DB schema error: {ex}")
        db.connection.rollback()
    else:
        logging.info(f"Current DB version = {db_version}")
        db.execute(f"PRAGMA user_version={db_version}", commit=True)
