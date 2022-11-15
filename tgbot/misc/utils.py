import random
from string import printable


def generate_telegram_cache_defense() -> str:
    allowed_chars = printable.replace('\t\n\r\v\f', '')
    return (
        random.choice(allowed_chars) + random.choice(allowed_chars)
    )