from fastapi import FastAPI

from app.log_replication import replicate_logs, get_logs_from_secondary
from app.utils import LogMessage

app = FastAPI()
logs = []
log_counter = 1


@app.get("/logs")
async def get_all_logs():
    all_logs = {'master_logs': logs}
    logs_from_secs = await get_logs_from_secondary()
    for secondary in logs_from_secs:
        all_logs.update(secondary)
    return all_logs


@app.post("/append")
async def append_log(log_message: LogMessage):
    global log_counter
    log_message.log_counter = log_counter
    logs.append(log_message)
    log_counter += 1
    await replicate_logs(log_message)
    return {'status': 'Ok'}
