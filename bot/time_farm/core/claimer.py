import aiohttp

from core import BaseClaimer
from ..headers import session_headers


class Claimer(BaseClaimer):

    async def run(self) -> None:
        tg_web_data = await self.get_tg_web_data()

        async with aiohttp.ClientSession(headers=session_headers) as http_client:
            while True:
                access_token = await self.login(http_client=http_client, tg_web_data=tg_web_data)
                pass
