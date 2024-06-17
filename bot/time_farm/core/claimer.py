import aiohttp
import asyncio

from time import time
from pyrogram import Client
from urllib.parse import quote

from core import BaseClaimer
from utils import logger
from exceptions import InvalidSession
from ..headers import session_headers
from ..config import settings


async def run_claimer(tg_client: Client):
    try:
        await Claimer(tg_client=tg_client).run()
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")


class Claimer(BaseClaimer):
    peer_name = 'TimeFarmBot'
    bot_url = 'https://tg-tap-miniapp.laborx.io/'

    async def login(self, http_client: aiohttp.ClientSession, tg_web_data: str):
        try:
            response = await http_client.post(url='https://tg-bot-tap.laborx.io/api/v1/auth/validate-init',
                                              data=tg_web_data)
            # return
            response_text = await response.text()
            # print(response_text)
            # response.raise_for_status()

            response_json = await response.json()

            # print(response_json)
            access_token = response_json['token']

            return access_token, response_json
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Access Token: {error}")
            await asyncio.sleep(delay=3)

    async def run(self) -> None:
        tg_web_data = await self.get_tg_web_data()

        async with aiohttp.ClientSession(headers=session_headers) as http_client:
            while True:
                access_token, account_info = await self.login(http_client=http_client, tg_web_data=tg_web_data)

                if not access_token:
                    await asyncio.sleep(delay=3)
                    continue

                http_client.headers["Authorization"] = f"Bearer {access_token}"

                balance_info = account_info['balanceInfo']

                balance = balance_info['balance']

                logger.info(f"{self.session_name} | Account Balance: <e>{balance}</e>")

                farming_info = await self.get_farming_info(http_client=http_client)

                active_farming_end = farming_info.get('activeFarmingStartedAt', None)
                if not active_farming_end:
                    logger.warning(f"{self.session_name} | No farming process")
                else:
                    logger.info(f"{self.session_name} | Have a farming process")

                    if time() > active_farming_end:
                        retry = 0
                        logger.info(f"{self.session_name} | Claim is ready, sleep 3s before claim")
                        await asyncio.sleep(delay=3)
                        while retry <= settings.TF_CLAIM_RETRY:
                            farming_data = await self.finish_farming(http_client=http_client)
                            if farming_data:
                                new_balance = farming_data['balance']
                                logger.success(f"{self.session_name} | Successful claim! | Balance: <e>{new_balance}")
                                break

                            logger.info(
                                f"{self.session_name} | Retry <y>{retry}</y> of <e>{settings.BLUM_CLAIM_RETRY}</e>")
                            retry += 1

    async def get_farming_info(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.post(url='https://tg-bot-tap.laborx.io/api/v1/farming/info')
            response.raise_for_status()

            response_json = await response.json()

            return response_json
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Farming Info: {error}")
            await asyncio.sleep(delay=3)

    async def finish_farming(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.post(url='https://tg-bot-tap.laborx.io/api/v1/farming/finish')
            response.raise_for_status()

            response_json = await response.json()

            return response_json
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Farming Info: {error}")
            await asyncio.sleep(delay=3)
