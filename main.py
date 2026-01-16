from os import getenv
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile

import requests
import re
import json
import dataclasses
from dotenv import load_dotenv

from urllib.parse import urlparse

load_dotenv()


@dataclasses.dataclass
class Result:
    status: bool
    message: str


def loader(url: str) -> Result:
    result = urlparse(url)
    if not (result.scheme and result.netloc):
        return Result(False, "Битая ссылка")

    s = requests.Session()

    headers = {
        'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 '
            'Safari/537.36',
    }

    response = s.get(url, headers=headers, allow_redirects=True)
    response_html = response.text
    re_compile = re.compile(r"<script id=\"__UNIVERSAL_DATA_FOR_REHYDRATION__\"[^>]*>(.*?)</script>", re.DOTALL)
    match = re_compile.search(response_html)
    if not match:
        return Result(False, "Видео не найдено")

    js: dict = json.loads(match.group(1))

    video_data = js.get("__DEFAULT_SCOPE__").get("webapp.video-detail").get("itemInfo").get("itemStruct")
    download_addr: str = video_data.get("video").get("downloadAddr")
    play_addr: str = video_data.get("video").get("playAddr")
    bitrate_info: list = video_data.get("video").get("bitrateInfo")
    if bitrate_info:
        bitrate_info_url = bitrate_info[0].get("PlayAddr").get("UrlList")[0]
        url_video = bitrate_info_url
    elif play_addr:
        url_video = play_addr
    elif download_addr:
        url_video = download_addr
    else:
        return Result(False, "Видео не найдено")

    video_headers = {
        'User-Agent': headers['User-Agent'],
        'Referer': 'https://www.tiktok.com/',
        'Accept': 'video/webm,video/ogg,video/*;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Range': 'bytes=0-',
        'Sec-Fetch-Dest': 'video',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'same-site',
    }
    response_video = s.get(url_video, headers=video_headers, stream=True, timeout=30)

    if response_video.status_code in [200, 206]:
        filename = f'tiktok_{video_data["id"]}.mp4'

        total_size = 0
        with open(filename, 'wb') as f:
            for chunk in response_video.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    total_size += len(chunk)

        return Result(True, filename)
    else:
        return Result(False, f"❌ Ошибка скачивания: {response_video.status_code}")


# Bot token can be obtained via https://t.me/BotFather
TOKEN = getenv("TOKEN")

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    # Most event objects have aliases for API methods that can be called in events' context
    # For example if you want to answer to incoming message you can use `message.answer(...)` alias
    # and the target chat will be passed to :ref:`aiogram.methods.send_message.SendMessage`
    # method automatically or call API method directly via
    # Bot instance: `bot.send_message(chat_id=message.chat.id, ...)`
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")


@dp.message()
async def echo_handler(message: Message) -> None:
    """
    Handler will forward receive a message back to the sender

    By default, message handler will handle all message types (like a text, photo, sticker etc.)
    """
    result = loader(message.text)
    if result.status:
        await message.answer_video(video=FSInputFile(result.message))
    else:
        await message.answer(result.message)


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
