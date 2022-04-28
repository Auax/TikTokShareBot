"""
By https://github.com/Auax - 2006
TikTok share bot based on https://github.com/Wizz1337
This bot actually uses async requests, these are faster than threads.
"""

import asyncio
import math
import os
import random
import ssl
import sys
import threading
import time
from typing import Dict, Any
from urllib.parse import urlparse

import aiohttp
from pystyle import Colors, Colorate, Write

from data.lists import *
from data.user_agents import USER_AGENTS

# region ssl certificate
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context


# endregion

def clear_console(): os.system("cls" if os.name == "nt" else "clear")


# region Classes
class ShareVariables:
    sent_requests = 0
    successful_requests = 0
    completed = False


class ShareBot:

    def __init__(self, url: str, share_vars: ShareVariables):
        self.clear_url_ = self.get_id_from_url(url)
        self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False))
        self.share_variables = share_vars
        self.session.cookie_jar.clear()

    def get_id_from_url(self, url: str):
        """
        Extract the ID from a url.
        :param url: link to TikTok video [str]
        :return: ID [str]
        """
        parsed_url = urlparse(url)  # Parse URL
        host = parsed_url.hostname.lower()
        if "vm.tiktok.com" == host or "vt.tiktok.com" == host:
            parsed_url = urlparse(
                self.session.head(self.get_id_from_url, verify=False, allow_redirects=True,
                                  timeout=5).url)
        return parsed_url.path.split("/")[3]

    async def send_share(self) -> int:
        """
        Send a share to a video
        :return: response.status [int]
        """

        platform_ = random.choice(PLATFORMS)
        os_version_ = random.randint(1, 12)
        device_type_ = random.choice(DEVICE_TYPES)
        device_id_ = random.randint(1000000000000000000, 9999999999999999999)
        headers = {
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "user-agent": random.choice(USER_AGENTS)
        }
        app_name_ = random.choice(["tiktok_web", "musically_go"])
        api_domain_ = random.choice(APP_DOMAINS)
        channel_ = random.choice(CHANNELS)
        URI = f"https://{api_domain_}/aweme/v1/aweme/stats/?" \
              f"channel={channel_}&" \
              f"device_type={device_type_}&" \
              f"device_id={device_id_}&" \
              f"os_version={os_version_}&" \
              f"version_code=220400&" \
              f"app_name={app_name_}&" \
              f"device_platform={platform_}&" \
              f"aid=1988"

        data = f"item_id={self.clear_url_}&share_delta=1"

        response = await self.session.post(
            url=URI,
            headers=headers,
            data=data)

        self.share_variables.sent_requests += 1
        if status := response.status == 200:
            self.share_variables.successful_requests += 1
        return status

    async def http_get_with_aiohttp_parallel(self, amount: int) -> None:
        """
        Execute several asynchronus aiohttp requests from a URL list
        :return: None
        """
        # TODO: look for a better implementation of this
        iters_ = 1
        range_ = amount
        if amount > 10000:
            iters_ = math.ceil(amount / 10000)
            range_ = 10000

        for i in range(iters_):
            await asyncio.gather(*[self.send_share() for _ in range(range_)])

    async def close_session(self):
        await self.session.close()


# endregion

def progress_thread(share_vars: ShareVariables) -> None:
    """
    Show requests/s and total requests performed so far.
    :param share_vars: ShareVariables class instance
    :return: None
    """
    while not share_vars.completed:
        start_req = share_vars.sent_requests
        time.sleep(1)
        end_req = share_vars.sent_requests
        elapsed_req = end_req - start_req
        print(
            f"Successful: {share_vars.successful_requests} ▉▉▉▉ Total: {share_vars.sent_requests} ▉▉▉▉ {elapsed_req} requests/s",
            end="\r")

    print(Colorate.Color(Colors.green, "Completed!"))


if __name__ == "__main__":
    while True:
        try:
            clear_console()
            video_url = str(Write.Input("Enter your video URL: ", Colors.red_to_purple, interval=0.0025))
            share_amount = int(Write.Input("Amount of shares: ", Colors.red_to_purple, interval=0.0025))
            break

        except ValueError:
            print(Colorate.Color(Colors.red, "Please input the correct values!", 1))
            time.sleep(2)

    clear_console()
    print(Colorate.Color(Colors.dark_red, "TikTok share bot by https://github.com/Auax!"))
    print("Press CTRL + C to stop!")

    share_variables = ShareVariables()


    async def async_run_shares():
        try:
            share_async = ShareBot(video_url, share_variables)

            await share_async.http_get_with_aiohttp_parallel(share_amount)
            await share_async.close_session()

        except ValueError:
            pass

        finally:
            raise KeyboardInterrupt


    try:
        # Progress thread
        threading.Thread(target=progress_thread, args=(share_variables,)).start()
        if os.name == "nt":
            # Fix Windows RuntimeError
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        # Run asynchronus shares function
        asyncio.run(async_run_shares())

    except KeyboardInterrupt:
        print(Colorate.Color(Colors.yellow, "Stopping async requests! You can close this window now!"))
        share_variables.completed = True
        sys.exit(1)
