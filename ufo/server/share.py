import asyncio
from typing import Optional


class SharedEventLoop:
    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        """
        Initialize the shared event loop.
        :param loop: Optional existing event loop to use. If None, a new event loop will be created.
        """

        self.loop = loop
