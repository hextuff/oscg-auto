import datetime
import os
import re
import zipfile

import aiohttp
import asyncio
import json
from pyppeteer import launch

target = 'https://osu.ppy.sh/scores/2803336922'
REGEXP = re.compile(r'.*?json-show.*?>(.*?)</script.*?', re.S)

proxy = 'http://127.0.0.1:20171'

AVATAR_SELECTOR = '#cover-settings-user > div.collapsible-container > div > div:nth-child(1) > label > input'
FLAG_SELECTOR = '#cover-settings-user > div.collapsible-container > div > div:nth-child(2) > div:nth-child(2) > div > button'
PLAYER_SELECTOR = '#cover-settings-user > div.collapsible-container > div > div:nth-child(2) > div:nth-child(1) > input'
SWITCH_SELECTORS = {
    'TIME_SWITCH_SELECTOR': '#cover-settings-difficulty > div.collapsible-container > div > div:nth-child(1) > div:nth-child(1) > div > label',
    'BPM_SWITCH_SELECTOR': '#cover-settings-difficulty > div.collapsible-container > div > div:nth-child(1) > div:nth-child(2) > div > label',
    'OD_SWITCH_SELECTOR': '#cover-settings-difficulty > div.collapsible-container > div > div:nth-child(2) > div:nth-child(3) > div > label',
    'HP_SWITCH_SELECTOR': '#cover-settings-difficulty > div.collapsible-container > div > div:nth-child(2) > div:nth-child(4) > div > label'
}
TIME_SELECTOR = '#cover-settings-difficulty > div.collapsible-container > div > div:nth-child(1) > div:nth-child(1) > input'
BPM_SELECTOR = '#cover-settings-difficulty > div.collapsible-container > div > div:nth-child(1) > div:nth-child(2) > input'
AR_SELECTOR = '#cover-settings-difficulty > div.collapsible-container > div > div:nth-child(2) > div:nth-child(1) > input'
CS_SELECTOR = '#cover-settings-difficulty > div.collapsible-container > div > div:nth-child(2) > div:nth-child(2) > input'
OD_SELECTOR = '#cover-settings-difficulty > div.collapsible-container > div > div:nth-child(2) > div:nth-child(3) > input'
HP_SELECTOR = '#cover-settings-difficulty > div.collapsible-container > div > div:nth-child(2) > div:nth-child(4) > input'
STAR_SELECTOR = '#cover-settings-difficulty > div.collapsible-container > div > div:nth-child(3) > div:nth-child(1) > input'
DIFF_SELECTOR = '#cover-settings-difficulty > div.collapsible-container > div > div:nth-child(3) > div:nth-child(2) > input'
MODS_SELECTORS = {
    'EZ': '#mod-select-ez',
    'NF': '#mod-select-nf',
    'HT': '#mod-select-ht',
    'HD': '#mod-select-hd',
    'HR': '#mod-select-hr',
    'DT': '#mod-select-dt',
    'NC': '#mod-select-nc',
    'FL': '#mod-select-fl',
    'SD': '#mod-select-sd',
    'PF': '#mod-select-pf',
    'RX': '#mod-select-rx',
    'AP': '#mod-select-ap',
    'SO': '#mod-select-so',
    'V2': '#mod-select-v2'
}

PP_SELECTOR = '#cover-settings-score > div.collapsible-container > div > div:nth-child(1) > input'
SCORE_STATUS_SELECTOR = '#cover-settings-score > div.collapsible-container > div > div:nth-child(2) > div > div > button'
MISS_SELECTOR = '#cover-settings-score > div.collapsible-container > div > div:nth-child(2) > div > input'
RANK_SELECTOR = '#cover-settings-score > div.collapsible-container > div > div:nth-child(3) > div:nth-child(1) > input'
ACC_SELECTOR = '#cover-settings-score > div.collapsible-container > div > div:nth-child(3) > div:nth-child(2) > input'
PERFECT_SELECTOR = '#cover-settings-score > div.collapsible-container > div > div:nth-child(4) > div:nth-child(1) > label'
COMBO_SELECTOR = '#cover-settings-score > div.collapsible-container > div > div:nth-child(4) > div:nth-child(2) > input'

TITLE_SELECTOR = '#cover-settings-beatmap > div.collapsible-container > div > div:nth-child(1) > input'
BACKGROUND_SELECTOR = '#cover-settings-beatmap > div.collapsible-container > div > div:nth-child(2) > label > input'
BEATMAP_STATE_SELECTOR = '#cover-settings-beatmap > div.collapsible-container > div > div:nth-child(3) > div > button'

COMMENT_SELECTOR = '#cover-settings-comment > div.collapsible-container > textarea'


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get(target, proxy=proxy) as resp:
            # print(resp.status)
            content = await resp.text()
            data = json.loads(REGEXP.findall(content)[0].strip())
            # print(data)
            # browser = await launch()
            # page = await browser.newPage()
            # await page.goto('https://a.yasunaori.be/osu-score-cover-generator/')
            # await page.screenshot({'path': 'example.png'})
            # await browser.close()
        # download all data needed
        await download_file(data['user']['avatar_url'], 'avatar.jpg')
        bg = await get_background(data['beatmapset']['id'], data['beatmap']['version'])


        browser = await launch(headless=False)
        page = await browser.newPage()
        await page.goto('https://a.yasunaori.be/osu-score-cover-generator/')
        await asyncio.sleep(3)
        # player info
        await upload_image(page, AVATAR_SELECTOR, './avatar.jpg')
        await choose(page, FLAG_SELECTOR, data['user']['country']['name'])
        await set_value(page, PLAYER_SELECTOR, data['user']['username'])
        # difficulty info
        for key in SWITCH_SELECTORS:
            await (await page.querySelector(SWITCH_SELECTORS[key])).click()
        min = data['beatmap']['hit_length'] // 60
        sec = data['beatmap']['hit_length'] % 60
        await set_value(page, TIME_SELECTOR, f'{min}:{sec}')
        await set_value(page, BPM_SELECTOR, str(data['beatmap']['bpm']))
        await set_value(page, AR_SELECTOR, str(data['beatmap']['ar']))
        await set_value(page, CS_SELECTOR, str(data['beatmap']['cs']))
        await set_value(page, OD_SELECTOR, str(data['beatmap']['accuracy']))
        await set_value(page, HP_SELECTOR, str(data['beatmap']['drain']))
        await set_value(page, STAR_SELECTOR, str(data['beatmap']['difficulty_rating']))
        await set_value(page, DIFF_SELECTOR, data['beatmap']['version'])
        for mod in data['mods']:
            name = mod['acronym']
            if name in MODS_SELECTORS:
                await (await page.querySelector(MODS_SELECTORS[name])).click()
        # score info
        await set_value(page, PP_SELECTOR, str(round(data['pp'], 0)))
        if 'miss' in data['statistics']:
            await choose(page, SCORE_STATUS_SELECTOR, 'miss')
            await set_value(page, MISS_SELECTOR, str(data['statistics']['miss']))
        elif data['accuracy'] == 1:
            await choose(page, SCORE_STATUS_SELECTOR, 'ss')
            await (await page.querySelector(PERFECT_SELECTOR)).click()
        else:
            await choose(page, SCORE_STATUS_SELECTOR, 'fc')
        await set_value(page, RANK_SELECTOR, str(data['rank_global']))
        await set_value(page, ACC_SELECTOR, str(round(data['accuracy']*100, 2)))
        await set_value(page, COMBO_SELECTOR, str(data['max_combo']))

        # beatmap info
        await set_value(page, TITLE_SELECTOR, data['beatmapset']['title'])
        await upload_image(page, BACKGROUND_SELECTOR, bg)
        await choose(page, BEATMAP_STATE_SELECTOR, data['beatmapset']['status'])

        # comment info
        await set_value(page, COMMENT_SELECTOR, '(。・ω・。)')


        await asyncio.sleep(60)
        await browser.close()


async def upload_image(page, selector: str, path: str):
    upload_element = await page.querySelector(selector)
    await upload_element.uploadFile(path)


async def choose(page, selector: str, option: str):
    flag_button = await page.querySelector(selector)
    await flag_button.click()
    options = await page.querySelectorAll('.dropdown-item')
    options = {(await page.evaluate('(element) => element.textContent', op)).lower(): op for op in options}
    await options[option.lower()].click()


async def set_value(page, selector: str, value: str):
    element = await page.querySelector(selector)
    await page.evaluate(f'(ele) => ele.value = ""', element)
    await element.type(value)


async def download_file(url, save_path):
    print(f'[+] downloading {url}')
    async with aiohttp.ClientSession() as session:
        async with session.get(url, proxy=proxy) as response:
            # Check if the request was successful
            if response.status == 200:
                # Get the file size from the response headers
                total_size = int(response.headers.get("Content-Length", 0))
                downloaded = 0

                # Open the file for writing
                with open(save_path, "wb") as f:
                    # Read the response in chunks and write to the file
                    while True:
                        chunk = await response.content.read(4096)  # Read 4KB at a time
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        # Print the download progress
                        # print(f"Downloaded {downloaded}/{total_size} bytes")
            else:
                print(f"Error downloading file: {response.status}")


async def download_beatmap(sid: int):
    await download_file(
        f'https://txy1.sayobot.cn/beatmaps/download/novideo/{sid}?server=auto',
        f'./beatmaps/{sid}.osz'
    )
    osz = zipfile.ZipFile(f'./beatmaps/{sid}.osz')
    print(f'[+] decompressing beatmap: {sid}')
    osz.extractall(f'./beatmaps/{sid}')
    osz.close()
    os.remove(f'./beatmaps/{sid}.osz')


BACKGROUND_REGEXP = re.compile(r'.*?Events.*?0,0,"(.*?)".*?', re.S)


async def get_background(sid: int, version: str) -> str:
    await download_beatmap(sid)
    files = [f for f in os.listdir(f'./beatmaps/{sid}') if f.endswith('.osu') and version in f]
    with open(f'./beatmaps/{sid}/{files[0]}', "r", encoding='utf-8') as osu:
        content = osu.read()
        bg = BACKGROUND_REGEXP.findall(content)[0]
    print(f'[+] found background: {bg}')
    return f'./beatmaps/{sid}/{bg}'

asyncio.run(main())
