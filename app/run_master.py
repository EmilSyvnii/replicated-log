import json
from typing import Union

import requests
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
    global log_counter
    log_message.log_counter = log_counter
    logs.append(log_message)
    log_counter += 1
    await replicate_logs(log_message)
    return {'status': 'Ok'}


async def replicate_logs(log_message: LogMessage):
    logger.info(f'Replicating log {log_message}')
    post_data = log_message.dict()
    logger.info(f'Post_data: {post_data}, type {type(post_data)}')
    response = requests.post(
        url='http://secondary_node_1:8001/append',
        data=json.dumps(post_data),
    )
    logger.info(f'Response status: {response.status_code}, message: {response.text}')
