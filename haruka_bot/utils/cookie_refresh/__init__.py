import re
import time
import execjs
import base64
from httpx import AsyncClient
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
from Crypto.PublicKey import RSA


class CookieRefresher:
    def __init__(self, username: str, password: str):
        self.__username = username
        self.__password = password
        self.__client = AsyncClient(timeout=10)
        self.__token = ""
        self.__gt = ""
        self.__challenge = ""
        self.__pic_url = ""
        self.__ccc = []
        self.__sss = ""
        self.__callback = ""
        self.__position = ""
        self.__validate = ""
        self.__salt = ""
        self.__key = ""

    async def refresh(self):
        await self.__get_captcha()
        await self.__check()
        await self.__get_position()
        time.sleep(3)
        await self.__crack_geetest()
        return await self.__login(self.__username, self.__password)

    # 申请极验数据
    async def __get_captcha(self):
        url = "https://passport.bilibili.com/x/passport-login/captcha?source=main_web"
        resp = await self.__client.get(url)
        geetest = resp.json()["data"]["geetest"]
        self.__token = resp.json()["data"]["token"]
        self.__gt = geetest["gt"]
        self.__challenge = geetest["challenge"]

    # 验证极验参数并获得验证码url等计算参数
    async def __check(self):
        t = int(time.time() * 1000)
        url = "https://api.geetest.com/get.php?" \
              "gt={}&challenge={}&lang=zh-cn&pt=3&client_type=web&w=&callback=geetest_{}"\
            .format(self.__gt, self.__challenge, t)
        await self.__client.get(url)
        url = "https://api.geetest.com/ajax.php?" \
              "gt={}&challenge={}&lang=zh-cn&pt=3&client_type=web&w=&callback=geetest_{}"\
            .format(self.__gt, self.__challenge, t)
        await self.__client.get(url)
        url = "https://api.geetest.com/get.php?is_next=true&type=click&gt={}&challenge={}&lang=zh-cn&https=false" \
              "&protocol=https%3A%2F%2F&offline=false&product=embed&api_server=api.geetest.com&isPC=true" \
              "&autoReset=true&width=100%25&callback=geetest_{}".format(self.__gt, self.__challenge, t)
        resp = await self.__client.get(url)
        pic = re.findall(r"\"pic\": \"(.*?)\"", resp.text)[0]
        self.__pic_url = "https://static.geetest.com" + pic
        self.__ccc = [int(x) for x in re.findall(r"\"c\": \[(.*?)\]", resp.text)[0].split(",")]
        self.__sss = re.findall(r"\"s\": \"(.*?)\"", resp.text)[0]
        self.__callback = "geetest_" + re.findall(r"geetest_(.*?)\(", resp.text)[0]

    # 请求识别验证码，获取坐标
    async def __get_position(self):
        url = "http://127.0.0.1:8000/clickOn"
        post_data = {
            "dataType": 1,
            "imageSource": self.__pic_url,
            "imageID": "string"
        }
        resp = await self.__client.post(url, json=post_data, headers={"Content-Type": "application/json"}, timeout=10)
        raw_position = resp.json()["data"]
        self.__position = self.__pos_convert(raw_position)

    # 破解极验获取validate
    async def __crack_geetest(self):
        context = execjs.compile(self.__read_file("./geetest_v3.js"))
        w = context.call("get_w", self.__position, self.__pic_url, self.__gt, self.__challenge, self.__ccc, self.__sss)
        url = "https://api.geetest.com/ajax.php"
        params = (
            ("gt", self.__gt),
            ("challenge", self.__challenge),
            ("lang", "zh-cn"),
            ("pt", 0),
            ("client_type", "web"),
            ("w", w),
            ("callback", self.__callback)
        )
        resp = await self.__client.get(url, params=params)
        self.__validate = re.findall(r"\"validate\": \"(.*?)\"", resp.text)[0]

    # 登录获取cookies
    async def __login(self, username, password):
        # 获取加密秘钥和盐
        url = "https://passport.bilibili.com/x/passport-login/web/key"
        resp = await self.__client.get(url)
        data = resp.json()["data"]
        salt = data["hash"]
        key = data["key"]
        cipher = self.__encrypt(key, salt + password)

        # 登录
        url = "https://passport.bilibili.com/x/passport-login/web/login"
        headers = {
            "Origin": "https://passport.bilibili.com",
            "Referer": "https://passport.bilibili.com/h5-app/passport/login",
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Mobile Safari/537.36",
            "Cookie": "buvid3=4A075D68-5D0B-D876-D88E-7D90DB4F1AF177842infoc; b_nut=1678161377; "
                      "_uuid=F25CA10E10-112E-79D2-583F-316E1B25A541078413infoc; home_feed_column=5; "
                      "rpdid=|(J~RYuR~)k|0J'uY~)uYuJ)Y; buvid_fp_plain=undefined; b_ut=5; i-wanna-go-feeds=-1; "
                      "i-wanna-go-back=2; hit-dyn-v2=1; buvid4=79201CCF-EE07-3F5F-8F7F-133459DCC9AB79670-023030711"
                      "-YqP%2BXrgApe6oZ8UlS%2BhKfg%3D%3D; LIVE_BUVID=AUTO8916781616663678; nostalgia_conf=-1; "
                      "hit-new-style-dyn=1; balh_server_inner=__custom__; balh_is_closed=; CURRENT_BLACKGAP=0; "
                      "CURRENT_FNVAL=4048; fingerprint=62dd5beb5f5b064c8ab1145eff902633; dy_spec_agreed=1; "
                      "CURRENT_PID=b8fe2bb0-ca21-11ed-a0d6-1fe16abf813c; CURRENT_QUALITY=80; "
                      "buvid_fp=62dd5beb5f5b064c8ab1145eff902633; FEED_LIVE_VERSION=V8; header_theme_version=CLOSE; "
                      "bp_video_offset_145892029=801461324319031300; PVID=1; b_lsid=A185ED10E_18875EAC605; sid=73xgqjp3"
        }
        post_data = {
            "username": username,
            "password": cipher,
            "keep": "true",
            "token": self.__token,
            "challenge": self.__challenge,
            "validate": self.__validate,
            "seccode": self.__validate + "|jordan",
            "go_url": "https://passport.bilibili.com/login"
        }
        resp = await self.__client.post(url, headers=headers, data=post_data)
        await self.__client.aclose()
        print(resp.text)
        cookies = resp.cookies
        ret = {}
        if cookies.__len__() != 0:
            ret = {
                "sid": cookies["sid"],
                "DedeUserID": cookies["DedeUserID"],
                "DedeUserID__ckMd5": cookies["DedeUserID__ckMd5"],
                "SESSDATA": cookies["SESSDATA"],
                "bili_jct": cookies["bili_jct"]
            }
        return ret

    # 坐标值转换
    @staticmethod
    def __pos_convert(raw):
        position = ""
        for x in raw:
            c_x = int(round((x[0] + x[2]) / 2 / 333.375 * 100 * 100, 0))
            c_y = int(round((x[1] + x[3]) / 2 / 333.375 * 100 * 100, 0))
            position += str(c_x) + "_" + str(c_y) + ","
        position = position[:-1]
        # print(position)
        return position

    # 明文密码加密
    @staticmethod
    def __encrypt(publickey, raw):
        rsa_key = RSA.importKey(publickey)
        cipher = Cipher_pkcs1_v1_5.new(rsa_key)
        raw = str(raw)
        cipher_text = base64.b64encode(cipher.encrypt(raw.encode()))
        return cipher_text.decode()

    # 文件读取
    @staticmethod
    def __read_file(file_name):
        with open(file_name, "r", encoding="UTF-8") as file:
            result = file.read()
        return result

