import os
from types import SimpleNamespace

from environs import Env


class Config(SimpleNamespace):
    token: str
    super_admin: int
    admin_ids: list[int]
    guide_ids: list[int]
    db_path: str
    credential_file: str


def load_config(path: str | None = None) -> Config:
    env: Env = Env()
    if path:
        env.read_env(path)

    return Config(
        token=env('BOT_TOKEN'),
        super_admin=env.int('SUPER_ADMIN'),
        admin_ids=env.list('ADMIN_IDS', subcast=int),
        guide_ids=env.list('GUIDE_IDS', subcast=int),
        db_path=env('BOT_DB_PATH', default='data/slavna.db'),
        credential_file=env('GOOGLE_CREDS'),

        # email
        hostname=env('EMAIL_HOST'),
        port=int(env('EMAIL_PORT')),
        email_username=env('EMAIL_HOST_USER'),
        email_password=env('EMAIL_HOST_PASSWORD'),
        use_tls=env('EMAIL_USE_SSL', 'True') == 'True',
    )


config = load_config(
    path='.env' if os.path.exists('.env') else None
)
