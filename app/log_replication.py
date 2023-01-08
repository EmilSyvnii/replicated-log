import asyncio
import json

import aiohttp

from app.config import logger
from app.utils import LogMessage, AiohttpClient

secondary_nodes_urls = [
    'http://secondary_node_1:8001/{path}',
    'http://secondary_node_2:8002/{path}',
]


async def replicate_logs(log_message: LogMessage):
    logger.info(f'Replicating log {log_message}')
    write_concern = log_message.write_concern
    if write_concern not in (1, 2, 3):
        logger.info(f'Invalid write concern value: {write_concern}')
        return

    logger.info(f'Processing with write concern {write_concern}')
    post_data = json.dumps(log_message.dict())   # check if it is needed to convert to dict and back to json
    logger.info(f'Post_data: {post_data}')
    tasks = []
    for url in secondary_nodes_urls:
        request_url = url.format(path='append')
        tasks.append(send_log(AiohttpClient.aiohttp_session, post_data, request_url))

    if write_concern == 1:
        return await send_and_return(tasks)

    if write_concern == 2:
        return await return_first_completed(tasks)

    # write concern 3
    return await asyncio.gather(*tasks)


async def send_and_return(task_list):
    """ Write concern 1:
        send requests to replicate on secondaries and return without waiting for any responses
    """
    for coro in task_list:
        background_tasks = set()
        task = asyncio.create_task(coro)
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)
    return


async def return_first_completed(task_list):
    """ Write concern 2:
        send requests to replicate on secondaries and return once at least one of the secondaries returns.
        The remaining request will be finished on the background.
    """
    done, pending = await asyncio.wait(task_list, return_when=asyncio.FIRST_COMPLETED)
    logger.info(f'Done first URL')
    for response in done:
        logger.info(f'Results: {response.result()}')
    if pending:
        logger.info(f'Running remaining URL')

    return


async def send_log(session: aiohttp.ClientSession, post_data: str, url: str):
    response = await session.post(
        url=url,
        json=json.loads(post_data),
    )
    return response


async def get_logs_from_secondary():
    tasks = []
    for index, url in enumerate(secondary_nodes_urls):
        url_name = f'secondary_node_{index + 1}'
        tasks.append(get_logs(AiohttpClient.aiohttp_session, url.format(path='logs'), url_name))
    results = await asyncio.gather(*tasks)
    return results


async def get_logs(session: aiohttp.ClientSession, url: str, url_name: str):
    response = await session.get(url=url)
    json_data = await response.json()
    return {url_name: json_data}


def get_replicated_logs(master_logs: list, secondary_nodes: list):
    """ Compare master logs with the logs from secondaries.
        Return only the logs that are replicated on all the nodes.
    """
    replicated_logs = []
    logger.info(f'Master logs: {master_logs}')
    for ind, log in enumerate(master_logs):
        is_replicated = True
        for secondary_node in secondary_nodes:
            for secondary_logs in secondary_node.values():
                try:
                    secondary_log_counter = secondary_logs[ind]['log_counter']
                    master_log_counter = log.log_counter
                    if secondary_log_counter != master_log_counter:
                        logger.info(
                            f'Master log counter {master_log_counter} does not '
                            f'match a log counter from secondary: {secondary_log_counter}'
                        )
                        is_replicated = False
                        break

                except IndexError:
                    logger.info(f'Seems like the log is missing on secondaries: {log}')
                    is_replicated = False
        if is_replicated:
            replicated_logs.append(log)
    return replicated_logs
