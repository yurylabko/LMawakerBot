class Messenger:
    key = None

    def __init__(self, reg) -> None:
        self.reg = reg

    def get_link(self):
        pass


class Viber(Messenger):
    key = "Viber"

    def get_link(self):
        return "viber://chat?number=%2B" + self.reg.user.phone_number[1:]


class Whatsapp(Messenger):
    key = "WhatsApp"

    def get_link(self):
        return "https://wa.me/" + self.reg.user.phone_number[1:]


class Telegram(Messenger):
    key = "Telegram"

    def get_link(self):
        return "tg://user?id=" + str(self.reg.user.id)


ALL_MSGRS = {c.key: c for c in Messenger.__subclasses__()}
