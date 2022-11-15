import logging
import re
import typing

from aiogram.dispatcher.filters import BoundFilter


class RegexpChoosenInlineResult(BoundFilter):
    def __init__(self, regexp: str):
        if not isinstance(regexp, typing.Pattern):
            regexp = re.compile(regexp, flags=re.IGNORECASE | re.MULTILINE)
        self.regexp = regexp

    async def check(self, obj):
        match = self.regexp.search(obj.query)
        if match: 
            return True
        return False

