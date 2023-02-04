import asyncio
import json
from uuid import uuid4

import aiohttp

from app.config import logger
from app.utils import LogMessage, AiohttpClient, NodeState

url_pattern = 'http://{node}:{port}/{path}'
secondary_nodes = [
    {
        'name': 'secondary_node_1',
        'port': 8001,
    },
    {
        'name': 'secondary_node_2',
        'port': 8002,
    },
]

secondary_nodes_state = {
    'secondary_node_1': NodeState.HEALTHY.value,
    'secondary_node_2': NodeState.HEALTHY.value,
}


async def replicate_logs(log_message: LogMessage):
    logger.info(f'Replicating log {log_message}')
    write_concern = log_message.write_concern
    if write_concern not in (1, 2, 3):
        logger.info(f'Invalid write concern value: {write_concern}')
        return

    logger.info(f'Processing with write concern {write_concern}')
    post_data = json.dumps(log_message.dict())
    logger.info(f'Post_data: {post_data}')
    tasks = []
    for node in secondary_nodes:
        request_url = url_pattern.format(
            node=node['name'],
            port=node['port'],
            path='append',
        )
        tasks.append(send_log(AiohttpClient.aiohttp_session, post_data, request_url, node['name']))

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


async def send_log(session: aiohttp.ClientSession, post_data: str, url: str, node_name: str):
    attempt = 0
    message_uuid = str(uuid4())
    json_post_data = json.loads(post_data)
    json_post_data['message_uuid'] = message_uuid
    while True:
        if secondary_nodes_state[node_name] == NodeState.HEALTHY.value:
            try:
                attempt += 1
                if attempt > 1:
                    logger.info(f'Retrying request for node {node_name}, attempt #{attempt}')
                response = await session.post(
                    url=url,
                    json=json_post_data,
                )
                return response

            except Exception as e:
                logger.info(f'Request Timeout for node {node_name}, error message {e}')

        else:
            # logger.info(f'{node_name} state is {secondary_nodes_state[node_name]}, sleeping for 1 sec.')
            await asyncio.sleep(1)


async def get_logs_from_secondary():
    tasks = []
    for node in secondary_nodes:
        node_name = node['name']
        url = url_pattern.format(
            node=node_name,
            port=node['port'],
            path='logs',
        )
        tasks.append(get_logs(AiohttpClient.aiohttp_session, url, node_name))
    results = await asyncio.gather(*tasks)
    return results


async def get_logs(session: aiohttp.ClientSession, url: str, node_name: str):
    response = await session.get(url=url)
    json_data = await response.json()
    return {node_name: json_data}


def get_replicated_logs(master_logs: list, secondary_node_logs: list):
    """ Compare master logs with the logs from secondaries.
        Return only the logs that are replicated on all the nodes.
    """
    replicated_logs = []
    logger.info(f'Master logs: {master_logs}')
    for ind, log in enumerate(master_logs):
        is_replicated = True
        for secondary_node in secondary_node_logs:
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


async def run_heartbeat_checker():
    while True:
        for node in secondary_nodes:
            node_name = node['name']
            url = url_pattern.format(
                node=node_name,
                port=node['port'],
                path='health',
            )
            asyncio.create_task(
                check_node_state(AiohttpClient.aiohttp_session, url, node_name)
            )
        await asyncio.sleep(10)


async def check_node_state(session: aiohttp.ClientSession, url: str, node_name: str):
    global secondary_nodes_state
    try:
        response = await session.get(url=url)
        status_code = response.status
    except Exception:
        status_code = 500
    logger.info(f'Checking heartbeat of {node_name}: {status_code}')
    if status_code == 200:
        secondary_nodes_state[node_name] = NodeState.HEALTHY.value
    else:
        current_state = secondary_nodes_state[node_name]
        if current_state == NodeState.HEALTHY.value:
            secondary_nodes_state[node_name] = NodeState.SUSPECTED.value
        else:
            secondary_nodes_state[node_name] = NodeState.UNHEALTHY.value

