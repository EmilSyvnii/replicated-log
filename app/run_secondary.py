from typing import Union

from fastapi import FastAPI
from pydantic import BaseModel

from app.config import logger


class LogMessage(BaseModel):
    message: str
    log_counter: Union[int, None] = None


app = FastAPI()
logs = []
log_counter = 1


@app.get("/logs")
async def get_all_logs():
    return {
        'logs': logs
    }


@app.post("/append")
async def append_log(log_message: LogMessage):
    logger.info(f'Received a new log: {log_message}')

    global log_counter
    log_message.log_counter = log_counter
    logs.append(log_message)
    log_counter += 1
    logger.info(f'Adding the log: {log_message}')
    logger.info(f'Logs list: {logs}')
    return {'status': 'Ok'}
