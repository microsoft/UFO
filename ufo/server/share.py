import asyncio
from typing import Optional


class SharedEventLoop:
    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        self.loop = loop
