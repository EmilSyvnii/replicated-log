import asyncio
import aiohttp
from pydantic import BaseModel
from typing import Union, Optional

# create event loop
loop = asyncio.get_event_loop()


# pydantic Model for POST requests
class LogMessage(BaseModel):
    message: str
    log_counter: Union[int, None] = None
    write_concern: Union[int, None] = None


class AiohttpClient:
    aiohttp_session: Optional[aiohttp.ClientSession] = None

    @classmethod
    def get_aiohttp_session(cls) -> aiohttp.ClientSession:
        if cls.aiohttp_session is None:
            cls.aiohttp_session = aiohttp.ClientSession()
        return cls.aiohttp_session

    @classmethod
    async def close_aiohttp_session(cls) -> None:
        if cls.aiohttp_session:
            await cls.aiohttp_session.close()
            cls.aiohttp_session = None
