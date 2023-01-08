from fastapi import FastAPI

from app.log_replication import (
    replicate_logs,
    get_logs_from_secondary,
    get_replicated_logs,
)
from app.utils import LogMessage, AiohttpClient
from app.config import logger

app = FastAPI(docs_url="/")
master_logs = []
log_counter = 1


@app.on_event("startup")
async def on_startup() -> None:
    logger.info('Starting Aiohttp Client')
    AiohttpClient.get_aiohttp_session()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info('Shutting Aiohttp Client')
    await AiohttpClient.close_aiohttp_session()


@app.get("/logs")
async def get_all_logs():
    logs_from_secs = await get_logs_from_secondary()
    replicated_logs = get_replicated_logs(master_logs, logs_from_secs)
    return replicated_logs


@app.post("/append")
async def append_log_with_wc(log_message: LogMessage):
    global log_counter
    log_message.log_counter = log_counter
    master_logs.append(log_message)
    log_counter += 1
    await replicate_logs(log_message)
    return {'status': 'Ok'}
