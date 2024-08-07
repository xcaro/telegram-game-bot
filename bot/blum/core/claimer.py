import asyncio
import json
import aiohttp
from time import time
from datetime import datetime
from random import randint

from exceptions import InvalidSession
from core import BaseGame
from utils import logger
from ..headers import session_headers
from ..config import settings


class BlumClaimer(BaseGame):
    peer_name = 'BlumCryptoBot'
    bot_url = 'https://telegram.blum.codes/'

    async def run(self) -> None:
        claim_time = 0
        is_farming = False

        tg_web_data = await self.get_tg_web_data()

        async with aiohttp.ClientSession(headers=session_headers) as http_client:
            while True:
                try:
                    # if time() - access_token_created_time >= 3600:
                    access_token = await self.login(http_client=http_client, tg_web_data=tg_web_data)

                    if not access_token:
                        await asyncio.sleep(delay=60)
                        continue

                    http_client.headers["Authorization"] = f"Bearer {access_token}"
                    # access_token_created_time = time()

                    # daily_reward = await self.get_daily_reward(http_client=http_client)
                    # print(daily_reward)

                    profile_balance = await self.get_profile_balance(http_client=http_client)

                    # print(profile_balance)
                    farming_data = profile_balance.get('farming', None)
                    game_tickets = profile_balance['playPasses']
                    available_balance = profile_balance["availableBalance"]
                    sleep_duration = 60

                    if farming_data:
                        is_farming = True

                        logger.info(f"{self.session_name} | Have a farming process")

                        earnings_rate = farming_data['earningsRate']
                        start_farming_time = int(str(farming_data['startTime'])[:-3])
                        claim_time = int(str(farming_data['endTime'])[:-3])
                        earning_balance = farming_data['balance']
                        sleep_duration = claim_time - time()

                        start_farming_date = datetime.fromtimestamp(start_farming_time).strftime(
                            '%Y-%m-%d %H:%M:%S')
                        end_farming_date = datetime.fromtimestamp(claim_time).strftime('%Y-%m-%d %H:%M:%S')

                        logger.info(f"{self.session_name} | Start farming at: <c>{start_farming_date}</c> | "
                                    f"Claim at: <c>{end_farming_date}</c>")
                        logger.info(
                            f"{self.session_name} | Farming: <g>+{earning_balance}</g> | Speed: <m>{earnings_rate}</m>")
                    else:
                        logger.info(f"{self.session_name} | No farming process")

                    logger.info(f"{self.session_name} | Available Balance: <e>{available_balance}</e> | "
                                f"Game ticket: <g>{game_tickets}</g>")

                    # profile_balance = await self.get_profile_balance(http_client=http_client)

                    daily_reward = await self.get_daily_reward(http_client=http_client)
                    if daily_reward:
                        if daily_reward['message'] == 'OK':
                            logger.success(f"{self.session_name} | Successfully claimed daily reward")
                        elif daily_reward['message'] == 'same day':
                            logger.success(f"{self.session_name} | Already claimed daily reward")
                        else:
                            logger.error(f"{self.session_name} | "
                                         f"Failed to claim daily reward, try again in a few minutes")
                    else:
                        logger.error(f"{self.session_name} | Cannot claim reward today")

                    if time() > claim_time and is_farming:
                        retry = 0
                        logger.info(f"{self.session_name} | Claim is ready, sleep 3s before claim")
                        await asyncio.sleep(delay=3)
                        while retry <= settings.BLUM_CLAIM_RETRY:
                            farming_data = await self.send_claim(http_client=http_client)
                            if farming_data:
                                # new_balance = farming_data['balance']
                                logger.success(f"{self.session_name} | Successful claim!")
                                is_farming = False
                                break

                            logger.info(
                                f"{self.session_name} | Retry <y>{retry}</y> of <e>{settings.BLUM_CLAIM_RETRY}</e>")
                            retry += 1

                    if not is_farming or not farming_data:
                        logger.info(f"{self.session_name} | Ready to start new farming, wait for 3s")
                        await asyncio.sleep(delay=3)

                        farm_response = await self.send_farm(http_client=http_client)
                        if farm_response:
                            logger.info(f"{self.session_name} | New farming process")

                            start_farming_date = datetime.fromtimestamp(
                                int(str(farm_response['startTime'])[:-3])).strftime('%Y-%m-%d %H:%M:%S')
                            claim_time = datetime.fromtimestamp(
                                int(str(farm_response['endTime'])[:-3])).strftime('%Y-%m-%d %H:%M:%S')

                            sleep_duration = int(str(farm_response['endTime'])[:-3]) - time()

                            logger.success(f"{self.session_name} | "
                                           f"Successfully start farming at: <c>{start_farming_date}</c>")
                            logger.success(f"{self.session_name} | "
                                           f"New claim at: <c>{claim_time}</c>")

                            is_farming = True
                        else:
                            logger.error(f"{self.session_name} | Starting error</c>")

                    if settings.BLUM_PLAY_GAME:
                        game_count = 0
                        while game_tickets > 0 and game_count < 5:
                            logger.info(f"{self.session_name} | "
                                        f"Game play after 3 seconds")
                            await asyncio.sleep(delay=3)

                            game_data = await self.trigger_to_play_game(http_client=http_client)

                            if game_data:
                                game_count += 1
                                logger.info(f"{self.session_name} | Playing game <y>{game_count}</y>")
                                await asyncio.sleep(delay=25)
                                previous_points = 0
                                while True:
                                    points = randint(255, 280)
                                    if points > previous_points:
                                        previous_points = points
                                    claim_response = await self.claim_playing_game(http_client=http_client,
                                                                                   game_id=game_data['gameId'],
                                                                                   points=previous_points)
                                    if claim_response == 'game session not finished':
                                        await asyncio.sleep(delay=1)
                                        continue
                                    elif claim_response == 'OK':
                                        logger.success(
                                            f"{self.session_name} | Game finished | Balance <g>+{previous_points}</g>")
                                        break
                                    elif claim_response == 'Token is invalid':
                                        access_token = await self.login(http_client=http_client,
                                                                        tg_web_data=tg_web_data)
                                        http_client.headers["Authorization"] = f"Bearer {access_token}"
                                        session_headers["Authorization"] = f"Bearer {access_token}"
                                        continue
                                    else:
                                        break

                            profile_balance = await self.get_profile_balance(http_client=http_client)
                            game_tickets = profile_balance['playPasses']
                            available_balance = profile_balance["availableBalance"]
                            logger.info(f"{self.session_name} | Available Balance: <e>{available_balance}</e> | "
                                        f"Game ticket: <g>{game_tickets}</g>")

                    sleep_time = sleep_duration + time()
                    sleep_time = datetime.fromtimestamp(sleep_time).strftime('%Y-%m-%d %H:%M:%S')
                    logger.info(f"{self.session_name} | sleep to: <r>{sleep_time}</r>")

                    await asyncio.sleep(delay=sleep_duration)

                except InvalidSession as error:
                    raise error

                except Exception as error:
                    logger.error(f"{self.session_name} | Unknown error: {error}")
                    await asyncio.sleep(delay=3)

    async def login(self, http_client: aiohttp.ClientSession, tg_web_data: str):
        try:
            response = await http_client.post(url='https://gateway.blum.codes/v1/auth/provider'
                                                  '/PROVIDER_TELEGRAM_MINI_APP',
                                              json={"query": tg_web_data})
            response_text = await response.text()
            response.raise_for_status()

            response_json = await response.json()
            access_token = response_json['token']['refresh']

            return access_token
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Access Token: {error}")
            await asyncio.sleep(delay=3)

    async def get_profile_data(self, http_client: aiohttp.ClientSession):
        while True:
            try:
                response = await http_client.get(url='https://gateway.blum.codes/v1/user/me')
                response_text = await response.text()
                if response.status != 422:
                    response.raise_for_status()

                response_json = json.loads(response_text)

                return response_json
            except Exception as error:
                logger.error(f"{self.session_name} | Unknown error while getting Profile Data: {error}")
                await asyncio.sleep(delay=3)

    async def get_profile_balance(self, http_client: aiohttp.ClientSession):
        while True:
            try:
                response = await http_client.get(url='https://game-domain.blum.codes/api/v1/user/balance')
                response_text = await response.text()
                if response.status != 422:
                    response.raise_for_status()

                response_json = json.loads(response_text)

                return response_json
            except Exception as error:
                logger.error(f"{self.session_name} | Unknown error while getting Profile Balance: {error}")
                await asyncio.sleep(delay=3)

    async def get_daily_reward(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.post(url='https://game-domain.blum.codes/api/v1/daily-reward?offset=-420')

            response_json = await response.json()

            return response_json
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Daily Reward: {error}")
            await asyncio.sleep(delay=3)

    async def send_claim(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.post(url='https://game-domain.blum.codes/api/v1/farming/claim')

            response_json = await response.json()

            return response_json
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Farming balance: {error}")
            await asyncio.sleep(delay=3)

    async def send_farm(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.post(url='https://game-domain.blum.codes/api/v1/farming/start')
            response.raise_for_status()

            response_json = await response.json()
            print(response_json)

            return response_json
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Farming balance: {error}")
            await asyncio.sleep(delay=3)

    async def trigger_to_play_game(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.post(url='https://game-domain.blum.codes/api/v1/game/play')
            response.raise_for_status()

            response_json = await response.json()

            return response_json
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while playing game: {error}")
            await asyncio.sleep(delay=3)

    async def claim_playing_game(self, http_client: aiohttp.ClientSession, game_id, points: int):
        try:
            response = await http_client.post(url='https://game-domain.blum.codes/api/v1/game/claim',
                                              json={"gameId": str(game_id), "points": points})
            response_text = await response.text()

            try:
                response_json = json.loads(response_text)
                return response_json.get("message")
            except ValueError:
                return response_text

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting game points: {error}")
            await asyncio.sleep(delay=3)
