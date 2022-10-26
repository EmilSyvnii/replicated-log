import asyncio
import json

import aiohttp

from app.config import logger
from app.utils import LogMessage

secondary_nodes_urls = [
    'http://secondary_node_1:8001/{path}',
    'http://secondary_node_2:8002/{path}',
]


async def replicate_logs(log_message: LogMessage):
    logger.info(f'Replicating log {log_message}')
    post_data = json.dumps(log_message.dict())   # check if it is needed to convert to dict and back to json
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in secondary_nodes_urls:
            request_url = url.format(path='append')
            tasks.append(send_log(session, post_data, request_url))
        results = await asyncio.gather(*tasks)
        for response in results:
            logger.info(f'Response {response.status}')
    return


async def send_log(session: aiohttp.ClientSession, post_data: str, url: str):
    response = await session.post(
        url=url,
        json=json.loads(post_data),
    )
    return response


async def get_logs_from_secondary():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for index, url in enumerate(secondary_nodes_urls):
            url_name = f'secondary_node_{index + 1}'
            tasks.append(get_logs(session, url.format(path='logs'), url_name))
        results = await asyncio.gather(*tasks)
        return results


async def get_logs(session: aiohttp.ClientSession, url: str, url_name: str):
    response = await session.get(url=url)
    json_data = await response.json()
    return {url_name: json_data}
