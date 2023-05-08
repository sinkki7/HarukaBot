from .bilibili_dynamic import Dynamic
from .bilibili_dynamic import Render
import requests
import json
import io


async def get_dynamic_pic(dynamic_id):
    """动态图片渲染"""
    url = f"https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail?dynamic_id={dynamic_id}"
    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; RMX1911) AppleWebKit/537.36 ",
        'Content-Type': "application/json"
    }
    res = requests.get(url=url, headers=headers, timeout=5)
    card = {}
    if res.status_code == 200:
        data = json.loads(res.text)
        card = data['data']['card']
    return await render_card(card)


async def render_card(card):
    card = Dynamic(**card)
    dynamic_img = await Render(card).render()
    img_bytes = io.BytesIO()
    dynamic_img.save(img_bytes, format="PNG")
    return img_bytes
