import asyncio
import os

from fastapi import FastAPI

from app.config import logger
from app.utils import LogMessage

SLEEP_FOR = os.environ.get('SLEEP_FOR')

app = FastAPI()
logs = []
received_message_uuids = []     # save every received message UUID to avoid duplications after retries


@app.get("/logs")
async def get_all_logs():
    logs_to_return = []
    for index, log in enumerate(logs):

        # check if the message order in the list matches the order messages have been sent in
        if log.log_counter == index + 1:
            logs_to_return.append(log)
        else:
            # break in case we miss a message
            break

    logger.info(f'Returning logs: {logs}')
    return logs_to_return


@app.post("/append")
async def append_log(log_message: LogMessage):
    logger.info(f'Received a new log: {log_message}')
    if SLEEP_FOR:
        logger.info(f'Sleeping for: {SLEEP_FOR} secs')
        await asyncio.sleep(int(SLEEP_FOR))

    message_uuid = log_message.message_uuid
    if message_uuid not in received_message_uuids:
        # insert the log into the list by message's counter to make sure we keep the same order as on the Master node
        logs.insert(int(log_message.log_counter) - 1, log_message)
        received_message_uuids.append(message_uuid)
        logger.info(f'Done replicating log: {log_message}')
    else:
        logger.info(f'Skip the log as it has already been replicated: {log_message}')
    return {'status': 'Ok'}


@app.get("/health")
async def check_heartbeat():
    return 200
