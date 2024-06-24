from abc import ABC, abstractmethod

import aiohttp

from urllib.parse import unquote
from pyrogram import Client
from pyrogram import types


class BaseGame:
    peer_name: str
    bot_url: str
    web_view_url: str
    session_name: str
    me: types.User

    def __init__(self, tg_client: Client, web_view_url: str, me):
        self.tg_client = tg_client
        self.session_name = tg_client.name + " | <y>" + self.peer_name + "</y>"

        self.web_view_url = web_view_url
        self.me = me

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
