import asyncio
from urllib.parse import unquote, quote

import aiohttp
import json

from aiocfscrape import CloudflareScraper
from better_proxy import Proxy
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait

from ..config import settings
from .headers import headers

from utils import generate_random_user_agent
from core import BaseGame
from utils import logger
from exceptions import InvalidSession

from random import randint, choice
from time import time


class CubesTapper(BaseGame):
    peer_name = 'cubesonthewater_bot'
    bot_url = 'https://www.thecubes.xyz/'

    async def login(self, http_client: aiohttp.ClientSession, init_data: str):
        try:
            async with http_client.post(url='https://server.questioncube.xyz/auth',
                                        json={'initData': init_data, 'ref': None}) as response:
                response_text = await response.text()
                app_user_data = json.loads(response_text)
                return app_user_data
        except Exception as error:
            logger.error(f"Auth request error happened: {error}")
            return None

    async def get_tg_x(self, http_client: aiohttp.ClientSession, token: str):
        try:
            async with http_client.post(url='https://server.questioncube.xyz/auth/trustmebro',
                                        json={'token': token, 'type': 'telegram'}) as response:
                response_text = await response.text()
                if response.status == 200:
                    async with http_client.post(url='https://server.questioncube.xyz/auth/trustmebro',
                                                json={'token': token, 'type': 'twitter'}) as response1:
                        response_text = await response1.text()
                        if response1.status == 200:
                            return True
        except Exception as error:
            logger.error(f"Get tg, x request error happened: {error}")
            return None

    async def mine(self, http_client: aiohttp.ClientSession, token: str):
        try:
            async with http_client.post(url='https://server.questioncube.xyz/game/mined',
                                        json={'token': token}) as response:
                response_text = await response.text()
                if response.status == 200:
                    mine_data = json.loads(response_text)
                    return mine_data
                else:
                    if response_text == '???????????????':
                        return None
                    elif response_text == '? banned ?':
                        return 'energy recovery'
                    elif response_text == 'Not enough energy':
                        return 'not enough'

        except Exception as error:
            logger.error(f"Mine request error happened: {error}")
            return None

    async def boost_pool(self, http_client: aiohttp.ClientSession, token: str, amount: int):
        try:
            async with http_client.post(url='https://server.questioncube.xyz/pools/boost',
                                        json={'amount': amount, 'token': token}) as response:
                response_text = await response.text()
                if response.status == 200:
                    boost_data = json.loads(response_text)
                    return boost_data
        except Exception as error:
            logger.error(f"Boost pool error happened {error}")
            return None

    async def claim_boxes(self, http_client: aiohttp.ClientSession, token: str):
        try:
            async with http_client.post(url='https://server.questioncube.xyz/pools/claim',
                                        json={'token': token}) as response:
                response_text = await response.text()
                data = json.loads(response_text)
                if (response_text == "{}"):
                    return None
                return data.get('boxesAmount')

        except Exception as error:
            logger.error(f"Claim request error happened: {error}")
            return None

    async def run(self) -> None:
        while True:
            bad_request_count = 0

            http_client = CloudflareScraper(headers=headers)

            tg_web_data = await self.get_tg_web_data()

            tg_web_data_parts = tg_web_data.split('&')
            query_id = tg_web_data_parts[0].split('=')[1]
            user_data = tg_web_data_parts[1].split('=')[1]
            auth_date = tg_web_data_parts[2].split('=')[1]
            hash_value = tg_web_data_parts[3].split('=')[1]

            user_data_encoded = quote(user_data)

            init_data = f"query_id={query_id}&user={user_data_encoded}&auth_date={auth_date}&hash={hash_value}"

            (http_client.headers
            ["User-Agent"]) = generate_random_user_agent(device_type='android', browser_type='chrome')

            app_user_data = await self.login(http_client=http_client, init_data=init_data)

            mining_delay = [0.8, 2, 2.8, 4, 5.2, 6, 6.8, 8]

            if app_user_data is not None:

                logger.info(f"{self.session_name} | Authorized")

                if app_user_data.get('banned_until_restore') == 'true':
                    logger.warning(f"{self.session_name} | "
                                   f"Energy recovery. Going sleep {1000 - int(app_user_data.get('energy'))} seconds")

                    boost_json = await self.boost_pool(http_client=http_client,
                                                       token=app_user_data.get('token'),
                                                       amount=app_user_data.get('drops_amount'))

                    if boost_json:
                        logger.success(f"{self.session_name} | Boosted pool for better rewards | invested: "
                                       f"{app_user_data.get('drops_amount')} | "
                                       f"total invest: "
                                       f"{boost_json.get('poolInvested')} | your invest: "
                                       f"{boost_json.get('userInvested')}")
                    await asyncio.sleep(1000 - int(app_user_data.get('energy')))

                status = await self.get_tg_x(http_client=http_client, token=app_user_data.get('token'))
                last_claim_time = time()
                time_before_claim = randint(a=settings.TIME_BETWEEN_RECEIVING_BOXES[0],
                                            b=settings.TIME_BETWEEN_RECEIVING_BOXES[1])
                while True:
                    try:
                        mine_data = await self.mine(http_client=http_client, token=app_user_data.get('token'))
                        if mine_data == 'energy recovery':
                            app_user_data = await self.login(http_client=http_client, init_data=init_data)
                            logger.warning(f"{self.session_name} | "
                                           f"Energy recovery. Going sleep {1000 - int(app_user_data.get('energy'))} "
                                           f"seconds")

                            boost_json = await self.boost_pool(http_client=http_client,
                                                               token=app_user_data.get('token'),
                                                               amount=app_user_data.get('drops_amount'))

                            if boost_json:
                                logger.success(f"{self.session_name} | Boosted pool for better rewards | invested: "
                                               f"{app_user_data.get('drops_amount')} | "
                                               f"total invest: "
                                               f"{boost_json.get('poolInvested')} | your invest: "
                                               f"{boost_json.get('userInvested')}")

                            await asyncio.sleep(1000 - int(app_user_data.get('energy')))
                            continue

                        if mine_data == 'not enough':
                            logger.warning(f'{self.session_name} | Not enough energy to mine block | '
                                           f'Going sleep 10 min')
                            await asyncio.sleep(60 * 10)
                            continue

                        elif mine_data is None:
                            if not self.tg_client.is_connected:
                                try:
                                    await self.tg_client.connect()

                                    bad_request_count += 1

                                    if bad_request_count != 10:
                                        continue

                                    elif bad_request_count == 10:
                                        await self.tg_client.send_message('cubesonthewater_bot', '/unban')
                                        bad_request_count = 0
                                        await self.tg_client.disconnect()
                                        continue
                                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                                    raise InvalidSession(self.session_name)

                        # elif mine_data is not None:
                        #     if (len(mine_data.get('mystery_ids')) > 0 and
                        #             int(mine_data.get('mystery_ids')[0]) == int(mine_data.get('mined_count'))):
                        #         logger.info(f"{self.session_name} | Mined <magenta>mystery box</magenta>! | Drops: "
                        #                     f"{mine_data.get('drops_amount')}; Energy: {mine_data.get('energy')}; "
                        #                     f"Boxes: {mine_data.get('boxes_amount')}")
                        #     else:
                        #         logger.info(f"{self.session_name} | Mined! | Drops: "
                        #                     f"{mine_data.get('drops_amount')}; "
                        #                     f"Energy: {mine_data.get('energy')}; Boxes: "
                        #                     f"{mine_data.get('boxes_amount')}")

                        sleep_between_mines = choice(mining_delay)
                        await asyncio.sleep(sleep_between_mines)

                        if (time() - last_claim_time) >= time_before_claim and (mine_data is not None or
                                                                                mine_data != {}):
                            boxes_before_claim = int(mine_data.get('boxes_amount'))
                            boxes_after_claim = await self.claim_boxes(http_client=http_client,
                                                                       token=app_user_data.get('token'))
                            if boxes_after_claim:
                                logger.info(f"{self.session_name} | Received "
                                            f"+{int(boxes_after_claim) - boxes_before_claim} mystery boxes")
                            else:
                                logger.info(f"{self.session_name} | No received mystery boxes")
                            time_before_claim = randint(a=settings.TIME_BETWEEN_RECEIVING_BOXES[0],
                                                        b=settings.TIME_BETWEEN_RECEIVING_BOXES[1])

                            last_claim_time = time()
                            sleep_between_mines = choice(mining_delay)
                            logger.info(f"{self.session_name} | Going sleep {sleep_between_mines} seconds")
                            await asyncio.sleep(sleep_between_mines)
                        elif mine_data is None or mine_data == {}:
                            continue

                    except InvalidSession as error:
                        raise error

                    except Exception as error:
                        logger.error(f"{self.session_name} | Unknown error: {error}")
                        await asyncio.sleep(delay=3)

            else:
                logger.info(f"{self.session_name} | No app_user_data found, restarting run method")
                await asyncio.sleep(5)


