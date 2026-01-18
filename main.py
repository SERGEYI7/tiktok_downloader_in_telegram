from os import getenv
import os
import asyncio
import logging
import sys
import time
from pprint import pprint

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile

from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
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
    message: str = ""
    path_video: str = ""
    path_screenshot: str = ""

def check_login(driver: uc.Chrome) -> Result:
    wait = WebDriverWait(driver, 20)
    page_lower = driver.page_source.lower()

    blocked_phrases = [
        'войдите в tiktok',
        'эта публикация содержит',
        'log in to tiktok',
        'sign in to continue'
    ]

    try:
        wait.until(EC.presence_of_element_located((By.ID, "loginContainer")))
        path = "message.png"
        driver.save_screenshot(path)
        return Result(False, f"Найдена фраза блокировки: {{phrase}}", "", path)
        # element = wait.until(
        #     EC.presence_of_element_located(
        #         (By.XPATH, "//div[contains(@class, 'DivLoginOptionContainer')]")
        #     )
        # )
    except:
        pass

    # for phrase in blocked_phrases:
    #     if phrase in page_lower:
    #         path = "message.png"
    #         driver.save_screenshot(path)
    #         try:
    #             wait.until(EC.presence_of_element_located((By.ID, "loginContainer")))
    #             return Result(False, f"Найдена фраза блокировки: {phrase}", "", path)
    #             # element = wait.until(
    #             #     EC.presence_of_element_located(
    #             #         (By.XPATH, "//div[contains(@class, 'DivLoginOptionContainer')]")
    #             #     )
    #             # )
    #         except:
    #             pass
            #     try:
            #
            #         # data_e2e = element.find_element(By.XPATH, ".//div[@data-e2e='channel-item']")
            #         data_e2e_wait = WebDriverWait(element, 20)
            #         data_e2e = data_e2e_wait.until(EC.element_to_be_clickable((By.XPATH, ".//div[@data-e2e='channel-item']")))
            #         print("Find data_e2e")
            #
            #         data_e2e.click()
            #         try:
            #             wait.until(
            #                 EC.presence_of_element_located(
            #                     (By.XPATH, "//div[contains(text(), 'Отсканируйте')]")
            #                 )
            #             )
            #             print("Появился сканируйте")
            #         except:
            #             print("не появился сканируйте")
            #         time.sleep(2)
            #         driver.save_screenshot(path)
            #     except:
            #         print("Не нашли data_e2e")
            #
            #     element_qr_text = element.find_element(By.XPATH, ".//div[contains(text(), 'Введите QR-код')]")
            #     if element_qr_text.is_selected():
            #         print("Is selected")
            #     else:
            #         print("Is not selected")
            #     # "//*[@id="loginContainer"]/div[1]/div/div"
            #     print("Найдена кнопка куар кода")
            # except:
            #     print("Не найдена кнопка куар кода")
            # return Result(False, f"Найдена фраза блокировки: {phrase}", "", path)
    return Result(True, "Non login form", "", "")

def loader(url: str) -> Result:
    result = urlparse(url)
    if not (result.scheme and result.netloc):
        return Result(False, "Битая ссылка", "", "")

    s = requests.Session()

    headers = {
        'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 '
            'Safari/537.36',
    }

    options = uc.ChromeOptions()
    options.add_argument("headless")

    driver = uc.Chrome(driver_executable_path=ChromeDriverManager().install(), options=options, version_main=None, use_subprocess=False)

    print("Открываю страницу...")
    driver.get(url)

    wait = WebDriverWait(driver, 20)
    wait.until(
        EC.presence_of_element_located((By.ID, "__UNIVERSAL_DATA_FOR_REHYDRATION__"))
    )

    result_check_login = check_login(driver)
    if not result_check_login.status:
        return result_check_login

#/////

    response_html = driver.page_source
    re_compile = re.compile(r"<script id=\"__UNIVERSAL_DATA_FOR_REHYDRATION__\"[^>]*>(.*?)</script>", re.DOTALL)
    match = re_compile.search(response_html)

    if not match:
        pprint(response_html)
        return Result(False, "Видео не найдено а именно __UNIVERSAL_DATA_FOR_REHYDRATION__", "", "")

    # find_title = driver.find_element(By.XPATH, "//*[@id=\"main-content-video_detail\"]/div/div[2]/div/div[1]/div[1]/div[3]/div/div/div[1]/p[1]")
    # if find_title:
    #     print("сработало")

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
        return Result(False, "Видео не найдено тупо ссылок нет")

    cookies = driver.get_cookies()

    for cookie in cookies:
        s.cookies.set(cookie['name'], cookie['value'])

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
        answer_video = await message.answer_video(video=FSInputFile(result.message))
        os.remove(result.message)
    else:
        await message.answer(result.message)
        proc = await message.answer_photo(FSInputFile(result.path_screenshot))
        sleep = await asyncio.sleep(1)
        # time.sleep(1)
        os.remove(result.path_screenshot)



async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
