import os
import glob
import asyncio
import argparse
import inspect
import importlib

from utils import logger
from configs import settings
from utils.registrator import register_sessions
from pyrogram import Client
from pyrogram.raw.functions.messages import RequestWebView

from core import BaseGame

start_text = """
Select an action:

    1. Create session
    2. Run clicker
"""


def get_session_names() -> list[str]:
    session_names = glob.glob('sessions/*.session')
    session_names = [os.path.splitext(os.path.basename(file))[0] for file in session_names]

    return session_names


async def get_tg_clients() -> list[Client]:
    session_names = get_session_names()

    if not session_names:
        raise FileNotFoundError("Not found session files")

    if not settings.API_ID or not settings.API_HASH:
        raise ValueError("API_ID and API_HASH not found in the .env file.")

    tg_clients = [Client(
        name=session_name,
        api_id=settings.API_ID,
        api_hash=settings.API_HASH,
        workdir='sessions/',
        plugins=dict(root='bot/plugins')
    ) for session_name in session_names]

    return tg_clients


async def process() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--action', type=int, help='Action to perform')

    logger.info(f"Detected {len(get_session_names())} sessions")

    action = parser.parse_args().action

    if not action:
        print(start_text)

        while True:
            action = input("> ")

            if not action.isdigit():
                logger.warning("Action must be number")
            elif action not in ['1', '2']:
                logger.warning("Action must be 1 or 2")
            else:
                action = int(action)
                break

    if action == 1:
        await register_sessions()
    elif action == 2:
        tg_clients = await get_tg_clients()

        await run_tasks(tg_clients=tg_clients)


def get_child_class_names(base_class):
    child_class_names = []
    for subclass in base_class.__subclasses__():
        module = importlib.import_module(subclass.__module__)
        cls = getattr(module, subclass.__name__)
        child_class_names.append(cls)
    return child_class_names


async def get_tasks_by_client(tg_client, classes: [BaseGame]):
    tasks = []
    if not tg_client.is_connected:
        await tg_client.connect()

    for cls in classes:
        peer_name = cls.peer_name
        bot_url = cls.bot_url
        session_name = tg_client.name + " | " + peer_name
        try:

            peer = await tg_client.resolve_peer(peer_name)
            web_view = await tg_client.invoke(RequestWebView(
                peer=peer,
                bot=peer,
                platform='android',
                from_bot_menu=False,
                url=bot_url
            ))

            me = await tg_client.get_me()

            auth_url = web_view.url
            tasks.append(asyncio.create_task(cls(tg_client=tg_client, web_view_url=auth_url, me=me).run()))

        except Exception as error:
            logger.error(f"{session_name} | {peer_name} | Unknown error during Authorization: {error}")
            await asyncio.sleep(delay=3)

    if tg_client.is_connected:
        await tg_client.disconnect()

    return tasks


async def run_tasks(tg_clients: list[Client]):
    tasks = []
    classes = get_child_class_names(BaseGame)
    for tg_client in tg_clients:
        tasks.extend(await get_tasks_by_client(tg_client, classes=classes))

    await asyncio.gather(*tasks)
