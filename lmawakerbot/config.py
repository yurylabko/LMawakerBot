from environs import Env
from dataclasses import dataclass


@dataclass
class TgBot:
    token: str
    admin_ids: list[int]


@dataclass
class Miscellaneuos:
    other_params: str = None


@dataclass
class Config:
    tg_bot: TgBot
    misc: Miscellaneuos
    use_redis: bool
    pg_url: str


def load_config(path: str = None):
    env = Env()
    env.read_env(path)
    return Config(
        tg_bot=TgBot(
            token=env.str("BOT_TOKEN"),
            admin_ids=list(map(int, env.list("ADMINS"))),
        ),
        misc=Miscellaneuos(),
        use_redis=env.bool("USE_REDIS"),
        pg_url=env.str("DATABASE_URL"),
    )
