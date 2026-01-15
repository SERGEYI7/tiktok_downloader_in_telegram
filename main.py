import requests
import re
import json
from pprint import pprint
from dotenv import load_dotenv
load_dotenv()
from os import getenv

url = "https://vt.tiktok.com/ZS5crJ686/"

print(getenv("TOKEN"))

s = requests.Session()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

response = s.get(url, headers=headers, allow_redirects=True)
html = response.text
re_compile = re.compile(r"<script id=\"__UNIVERSAL_DATA_FOR_REHYDRATION__\"[^>]*>(.*?)</script>", re.DOTALL)
match = re_compile.search(html)
if not match:
    print("Видео не найдено")
    exit()

js: dict = json.loads(match.group(1))

video_data = js.get("__DEFAULT_SCOPE__").get("webapp.video-detail").get("itemInfo").get("itemStruct")
downloadAddr: str = video_data.get("video").get("downloadAddr")
playAddr: str = video_data.get("video").get("playAddr")
bitrateInfo: list = video_data.get("video").get("bitrateInfo")
bitrateInfo_url = ""
if bitrateInfo:
    bitrateInfo_url = bitrateInfo[0].get("PlayAddr").get("UrlList")[0]

url_video = bitrateInfo_url

video_headers = {
    'User-Agent': headers['User-Agent'],
    'Referer': 'https://www.tiktok.com/',
    'Accept': 'video/webm,video/ogg,video/*;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Range': 'bytes=0-',  # Важно для некоторых CDN
    'Sec-Fetch-Dest': 'video',
    'Sec-Fetch-Mode': 'no-cors',
    'Sec-Fetch-Site': 'same-site',
}
response_video = s.get(url_video, headers=video_headers, stream=True, timeout=30)
# print(response_downloadAddr.text)

if response_video.status_code in [200, 206]:
    filename = f'tiktok_{video_data["id"]}.mp4'

    total_size = 0
    with open(filename, 'wb') as f:
        for chunk in response_video.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                total_size += len(chunk)
                print(f'\rСкачано: {total_size / 1024 / 1024:.2f} MB', end='')

    print(f'\n✓ Готово: {filename}')
else:
    print(f"❌ Ошибка скачивания: {response_video.status_code}")
    print(response_video.text[:1000])

# pprint(js.get("__DEFAULT_SCOPE__").get("webapp.video-detail").get("itemInfo").get("itemStruct").get("video"))

# print(response.history)
