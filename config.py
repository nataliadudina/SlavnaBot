from dataclasses import dataclass

from environs import Env


@dataclass
class TgBot:
    token: str  # Токен для доступа к телеграм-боту
    super_admin: int  # id суперадмина
    admin_ids: list[int]  # Список id администраторов бота
    guide_ids: list[int]  # Список гидов


def load_bot_config(path: str | None = None) -> TgBot:
    env: Env = Env()
    env.read_env(path)

    return TgBot(
        token=env('BOT_TOKEN'),
        super_admin=int(env('SUPER_ADMIN')),
        admin_ids=list(map(int, env.list('ADMIN_IDS'))),
        guide_ids=list(map(int, env.list('GUIDE_IDS')))
    )


# Инициализация конфигурации
bot_config = load_bot_config('.env')
