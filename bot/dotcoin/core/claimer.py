import asyncio
from time import time
from random import randint

import aiohttp
from better_proxy import Proxy
from pyrogram import Client

from .headers import headers
from core import BaseGame
from exceptions import InvalidSession
from utils import logger
from ..config import settings


class DotClaimer(BaseGame):
    peer_name = "dotcoin_bot"
    bot_url = "https://dot.dapplab.xyz/"

    async def login(self, http_client: aiohttp.ClientSession, tg_web_data: str):
        try:
            http_client.headers[
                "Authorization"] = f"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Impqdm5tb3luY21jZXdudXlreWlkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDg3MDE5ODIsImV4cCI6MjAyNDI3Nzk4Mn0.oZh_ECA6fA2NlwoUamf1TqF45lrMC0uIdJXvVitDbZ8"
            http_client.headers["Content-Type"] = "application/json"
            response = await http_client.post('https://jjvnmoyncmcewnuykyid.supabase.co/functions/v1/getToken',
                                              json={"initData": tg_web_data})
            response.raise_for_status()

            response_json = await response.json()

            return response_json['token']
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when getting access token: {error}")
            await asyncio.sleep(delay=3)

    async def get_profile_data(self, http_client: aiohttp.ClientSession) -> dict[str]:
        try:
            response = await http_client.post('https://jjvnmoyncmcewnuykyid.supabase.co/rest/v1/rpc/get_user_info',
                                              json={})
            response.raise_for_status()

            response_json = await response.json()

            return response_json
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when getting Profile Data: {error}")
            await asyncio.sleep(delay=3)

    async def get_tasks_data(self, http_client: aiohttp.ClientSession, is_premium: bool) -> dict[str]:
        try:
            response = await http_client.post('https://jjvnmoyncmcewnuykyid.supabase.co/rest/v1/rpc/get_filtered_tasks',
                                              json={"platform": "android", "locale": "en", "is_premium": is_premium})
            response.raise_for_status()

            response_json = await response.json()

            return response_json
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when getting Tasks Data: {error}")
            await asyncio.sleep(delay=3)

    async def complate_task(self, http_client: aiohttp.ClientSession, task_id: int) -> bool:
        try:
            response = await http_client.post('https://jjvnmoyncmcewnuykyid.supabase.co/rest/v1/rpc/complete_task',
                                              json={"oid": task_id})
            response.raise_for_status()

            response_json = await response.json()

            return response_json['success']
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when complate task: {error}")
            await asyncio.sleep(delay=3)

            return False

    async def upgrade_boosts(self, http_client: aiohttp.ClientSession, boost_type: str, lvl: int) -> bool:
        try:
            response = await http_client.post(f'https://jjvnmoyncmcewnuykyid.supabase.co/rest/v1/rpc/{boost_type}',
                                              json={"lvl": lvl})
            response.raise_for_status()

            response_json = await response.json()

            return response_json['success']
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when complate task: {error}")
            await asyncio.sleep(delay=3)

            return False

    async def save_coins(self, http_client: aiohttp.ClientSession, taps: int) -> bool:
        try:
            response = await http_client.post('https://jjvnmoyncmcewnuykyid.supabase.co/rest/v1/rpc/save_coins',
                                              json={"coins": taps})
            response.raise_for_status()

            response_json = await response.json()

            return response_json['success']

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when saving coins: {error}")
            await asyncio.sleep(delay=3)

            return False

    async def run(self) -> None:
        access_token_created_time = 0

        async with aiohttp.ClientSession(headers=headers) as http_client:

            while True:
                try:
                    if time() - access_token_created_time >= 3600:
                        tg_web_data = await self.get_tg_web_data()
                        access_token = await self.login(http_client=http_client,
                                                        tg_web_data=tg_web_data)

                        http_client.headers["Authorization"] = f"Bearer {access_token}"
                        headers["Authorization"] = f"Bearer {access_token}"

                        http_client.headers["X-Telegram-User-Id"] = str(self.me.id)
                        headers["X-Telegram-User-Id"] = str(self.me.id)

                        access_token_created_time = time()

                        profile_data = await self.get_profile_data(http_client=http_client)

                        balance = profile_data['balance']
                        daily_attempts = profile_data['daily_attempts']

                        logger.info(f"{self.session_name} | Balance: <c>{balance}</c>")
                        logger.info(f"{self.session_name} | Remaining attempts: <m>{daily_attempts}</m>")

                        tasks_data = await self.get_tasks_data(http_client=http_client,
                                                               is_premium=profile_data['is_premium'])

                        for task in tasks_data:
                            task_id = task["id"]
                            task_title = task["title"]
                            task_reward = task["reward"]
                            task_status = task["is_completed"]

                            if task_status is True:
                                continue

                            if task["url"] is None and task["image"] is None:
                                continue

                            task_data_claim = await self.complate_task(http_client=http_client, task_id=task_id)
                            if task_data_claim:
                                logger.success(f"{self.session_name} | Successful claim task | "
                                               f"Task Title: <c>{task_title}</c> | "
                                               f"Task Reward: <g>+{task_reward}</g>")
                                continue

                        for i in range(daily_attempts, 0, -1):
                            if i == 0:
                                logger.info(f"{self.session_name} | Minimum attempts reached: {i}")
                                logger.info(f"{self.session_name} | Next try to tap coins in 1 hour")
                                break

                            taps = randint(a=settings.RANDOM_TAPS_COUNT[0], b=settings.RANDOM_TAPS_COUNT[1])
                            status = await self.save_coins(http_client=http_client, taps=taps)
                            if status:
                                new_balance = balance + taps
                                logger.success(f"{self.session_name} | Successful Tapped! | "
                                               f"Balance: <c>{new_balance}</c> (<g>+{taps}</g>) | Remaining attempts: <e>{i}</e>")

                            sleep = randint(a=settings.SLEEP_BETWEEN_TAP[0], b=settings.SLEEP_BETWEEN_TAP[1])
                            logger.info(f"{self.session_name} | Sleep {sleep}s for next tap")
                            await asyncio.sleep(delay=sleep)

                    await asyncio.sleep(delay=1000)
                    profile_data = await self.get_profile_data(http_client=http_client)

                    balance = int(profile_data['balance'])
                    daily_attempts = int(profile_data['daily_attempts'])
                    multiple_lvl = profile_data['multiple_clicks']
                    attempts_lvl = profile_data['limit_attempts'] - 9

                    next_multiple_lvl = multiple_lvl + 1
                    next_multiple_price = (2 ** multiple_lvl) * 1000
                    next_attempts_lvl = attempts_lvl + 1
                    next_attempts_price = (2 ** attempts_lvl) * 1000

                    logger.info(f"{self.session_name} | Balance: <c>{balance}</c>")
                    logger.info(f"{self.session_name} | Remaining attempts: <m>{daily_attempts}</m>")

                    if (settings.AUTO_UPGRADE_TAP is True
                            and balance > next_multiple_price
                            and next_multiple_lvl <= settings.MAX_TAP_LEVEL):
                        logger.info(f"{self.session_name} | Sleep 5s before upgrade tap to {next_multiple_lvl} lvl")
                        await asyncio.sleep(delay=5)

                        status = await self.upgrade_boosts(http_client=http_client, boost_type="add_multitap",
                                                           lvl=multiple_lvl)
                        if status is True:
                            logger.success(f"{self.session_name} | Tap upgraded to {next_multiple_lvl} lvl")

                            await asyncio.sleep(delay=1)

                        continue

                    if (settings.AUTO_UPGRADE_ATTEMPTS is True
                            and balance > next_attempts_price
                            and next_attempts_lvl <= settings.MAX_ATTEMPTS_LEVEL):
                        logger.info(
                            f"{self.session_name} | Sleep 5s before upgrade limit attempts to {next_attempts_lvl} lvl")
                        await asyncio.sleep(delay=5)

                        status = await self.upgrade_boosts(http_client=http_client, boost_type="add_attempts",
                                                           lvl=attempts_lvl)
                        if status is True:
                            new_daily_attempts = next_attempts_lvl + 9
                            logger.success(
                                f"{self.session_name} | Limit attempts upgraded to {next_attempts_lvl} lvl (<m>{new_daily_attempts}</m>)")

                            await asyncio.sleep(delay=1)

                        continue

                except InvalidSession as error:
                    raise error

                except Exception as error:
                    logger.error(f"{self.session_name} | Unknown error: {error}")
                    await asyncio.sleep(delay=3)

                else:
                    logger.info(f"{self.session_name} | Sleep 1h")
                    await asyncio.sleep(delay=3600)
