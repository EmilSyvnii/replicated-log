import asyncio
from pydantic import BaseModel
from typing import Union

# create event loop
loop = asyncio.get_event_loop()


# pydantic Model for POST requests
class LogMessage(BaseModel):
    message: str
    log_counter: Union[int, None] = None
