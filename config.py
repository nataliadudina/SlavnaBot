from types import SimpleNamespace

from environs import Env


class Config(SimpleNamespace):
    token: str
    super_admin: int
    admin_ids: list[int]
    guide_ids: list[int]
    db_path: str


def load_config(path: str | None = None) -> Config:
    env: Env = Env()
    env.read_env(path)

    return Config(
        token=env('BOT_TOKEN'),
        super_admin=env.int('SUPER_ADMIN'),
        admin_ids=env.list('ADMIN_IDS', subcast=int),
        guide_ids=env.list('GUIDE_IDS', subcast=int),
        db_path=env('BOT_DB_PATH', default='slavna.db'),
    )


config = load_config('.env')
