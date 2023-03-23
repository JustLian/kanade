"かなではディスコードのボット。"
__all__ = ("cfg", "Colors", "hooks")


import json
from hikari import Color
from kanade.core import hooks


cfg = None


def update_cfg() -> None:
    "Updates madoka.cfg file"

    global cfg
    with open('./config.json', 'r', encoding='utf8') as f:
        cfg = json.load(f)


update_cfg()


class Colors:
    ERROR = Color.from_hex_code('8884ff')
    WAIT = Color.from_hex_code('fde2ff')
    WARNING = Color.from_hex_code('d7bce8')
    SUCCESS = Color.from_hex_code('f570a5')
