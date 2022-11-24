from dataclasses import dataclass
from pathlib import Path

from environs import Env


@dataclass
class DbConfig:
    host: str
    password: str
    user: str
    database: str


@dataclass
class TgBot:
    token: str
    admin_ids: list[int]
    use_redis: bool
    commands: dict[str, str]
    payments_provider_token: str

@dataclass
class Locale:
    domain: str
    dir: str

@dataclass
class LiqPay: 
    private_key: str
    public_key: str


@dataclass
class Miscellaneous:
    csrf_trusted_origins: list[str]
    other_params: str = None


@dataclass
class Redis:
    host: str
    port: int

    @property
    def url(self) -> str:
        return f"redis://{self.host}:{self.port}"


@dataclass
class Config:
    tg_bot: TgBot
    locale: Locale
    db: DbConfig
    liqpay: LiqPay
    redis: Redis
    misc: Miscellaneous


def load_config(path: str = None):
    env = Env()
    env.read_env(path)
    
    return Config(
        tg_bot=TgBot(
            token=env.str("BOT_TOKEN"),
            admin_ids=list(map(int, env.list("ADMINS"))),
            use_redis=env.bool("USE_REDIS"),
            payments_provider_token=env.str("PAYMENTS_PROVIDER_TOKEN"),
            commands=env.json("COMMANDS"),
        ),
        locale=Locale(
            domain=env.str('LOCALE_DOMAIN'),
            dir=Path(__file__).parent.parent / env.str('LOCALE_DIR')    
        ),
        liqpay=LiqPay(
            private_key=env.str('LIQPAY_PRIVATE_KEY'),
            public_key=env.str('LIQPAY_PUBLIC_KEY'),
        ),
        db=DbConfig(
            host=env.str("DB_HOST"),
            password=env.str("DB_PASS"),
            user=env.str("DB_USER"),
            database=env.str("DB_NAME"),
        ),
        redis=Redis(
            host=env.str("REDIS_HOST"),
            port=env.int("REDIS_PORT"),
        ),
        misc=Miscellaneous(
            csrf_trusted_origins=[i for i in env.list("CSRF_TRUSTED_ORIGINS") if i.startswith('http')],
        )
    )

