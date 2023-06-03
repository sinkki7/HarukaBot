from .bilibili_dynamic import Dynamic
from .bilibili_dynamic import Render
import requests
import json
import io
from ..utils.cookie_refresh import CookieRefresher
from ..config import plugin_config
from nonebot.log import logger


async def refresh_cookie(username, password):
    return await CookieRefresher(username, password).refresh()


def read_json_file(file_name):
    with open(file_name, "r", encoding="UTF-8") as file:
        result = file.read()
    return json.loads(result)


def write_json_file(data, file_name):
    json_data = json.dumps(data, indent=4)
    with open(file_name, "w", encoding="UTF-8") as file:
        file.write(json_data)


async def get_dynamic_pic(dynamic_id):
    """动态图片渲染"""
    url = f"https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail?dynamic_id={dynamic_id}"
    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; RMX1911) AppleWebKit/537.36 ",
        'Content-Type': "application/json"
    }
    cookies = read_json_file(plugin_config.bilibili_account_url)["cookies"]
    if cookies != {}:
        headers["Cookie"] = "SESSDATA=" + cookies["SESSDATA"] + ";"
    res = requests.get(url=url, headers=headers, timeout=5)
    card = {}
    try:
        if res.status_code == 200:
            data = json.loads(res.text)
            card = data['data']['card']
    except Exception as e:
        logger.error(f"获取动态详情失败：{e}")
        data = read_json_file(plugin_config.bilibili_account_url)
        cookies = await refresh_cookie(data["username"], data["password"])
        data["cookies"] = cookies
        write_json_file(data, plugin_config.bilibili_account_url)
    return await render_card(card)


async def render_card(card):
    if card != {}:
        card = Dynamic(**card)
        dynamic_img = await Render(card).render()
        img_bytes = io.BytesIO()
        dynamic_img.save(img_bytes, format="PNG")
        return img_bytes
