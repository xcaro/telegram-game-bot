from abc import ABC, abstractmethod

import aiohttp

from urllib.parse import unquote
from pyrogram import Client


class BaseGame:
    peer_name: str
    bot_url: str
    web_view_url: str
    session_name: str

    def __init__(self, tg_client: Client, web_view_url: str):
        self.tg_client = tg_client
        self.session_name = tg_client.name + " | " + self.peer_name

        self.web_view_url = web_view_url

    @abstractmethod
    async def run(self) -> None:
        pass

    @abstractmethod
    async def login(self, http_client: aiohttp.ClientSession, tg_web_data: str):
        pass

    async def get_tg_web_data(self):
        auth_url = self.web_view_url
        tg_web_data = unquote(
            string=unquote(
                string=auth_url.split('tgWebAppData=', maxsplit=1)[1].split('&tgWebAppVersion', maxsplit=1)[0]))
        return tg_web_data

    # async def get_tg_web_data(self):
    #     try:
    #         if not self.tg_client.is_connected:
    #             try:
    #                 await self.tg_client.connect()
    #             except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
    #                 raise InvalidSession(self.session_name)
    #
    #         peer = await self.tg_client.resolve_peer(self.peer_name)
    #         web_view = await self.tg_client.invoke(RequestWebView(
    #             peer=peer,
    #             bot=peer,
    #             platform='android',
    #             from_bot_menu=False,
    #             url=self.bot_url
    #         ))
    #
    #         auth_url = web_view.url
    #         tg_web_data = unquote(
    #             string=unquote(
    #                 string=auth_url.split('tgWebAppData=', maxsplit=1)[1].split('&tgWebAppVersion', maxsplit=1)[0]))
    #
    #         return tg_web_data
    #
    #     except Exception as error:
    #         logger.error(f"{self.session_name} | {self.peer_name} | Unknown error during Authorization: {error}")
    #         await asyncio.sleep(delay=3)
