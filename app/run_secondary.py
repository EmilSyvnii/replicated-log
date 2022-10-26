from fastapi import FastAPI

from app.config import logger
from app.utils import LogMessage

app = FastAPI()
logs = []


@app.get("/logs")
async def get_all_logs():
    logs_to_return = []
    for index, log in enumerate(logs):

        # check if the message order in the list matches the order messages have been sent in
        if log.log_counter == index + 1:
            logs_to_return.append(log)
        else:
            # break in case we miss some message
            break

    logger.info(f'Returning logs: {logs}')
    return logs_to_return


@app.post("/append")
async def append_log(log_message: LogMessage):
    logger.info(f'Received a new log: {log_message}')

    # insert the log into the list by message's counter to make sure we keep the same order as on the Master node
    logs.insert(int(log_message.log_counter) - 1, log_message)
    return {'status': 'Ok'}
