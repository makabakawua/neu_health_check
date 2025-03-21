import os
import json
import time
import requests
from bs4 import BeautifulSoup
from Crypto.Cipher import DES3
import base64
import binascii
from pysmx.SM3 import digest
import hashlib
import urllib.parse
import random

#snowland-smx
#pycryptodome


USERNAME = os.environ["USERNAME"]
PASSWORD = os.environ["PASSWORD"]

HOME = int(os.environ.get("HOME", "0"))

USER_PROVINCE = os.environ["USER_PROVINCE"]
MAP_LON = os.environ["MAP_LON"]
MAP_LAT = os.environ["MAP_LAT"]


def getDES3Token(text, key):
    #PKCS5Padding
    #字符串长度需要是8的倍数
    BS = 8
    pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
    unpad = lambda s : s[0:-ord(s[-1])]
    #注意3DES的MODE_CBC模式下只有前24位有意义
    #key和iv都需要是bytearray
    
    iv = b'01234567'
    #text也需要encode成bytearray
    plaintext = pad(text).encode()
    #使用MODE_CBC创建cipher
    cipher = DES3.new(key, DES3.MODE_CBC, iv)
    #加密
    result = cipher.encrypt(plaintext)
    result = binascii.b2a_hex(result)
    result = str(result, 'utf-8')
    return result.upper()
    
def getSM3Token(text):
    result = digest(text)
    result = binascii.b2a_hex(result)
    result = str(result, 'utf-8')
    return result
    
def getMD5Token(text):
    return hashlib.md5(text.encode(encoding="UTF-8")).hexdigest().upper()


def login(username, password) -> (int, requests.session):
    s = requests.Session()
    headers = {
        "user-agent": "okhttp/3.8.0"
    }
    login_url = "https://portal.neu.edu.cn/tp_up/up/mobile/ifs/" + getDES3Token("method=userLogin&id_number=" + username + "&pwd=" + password + "&mobile_device_uuid=" + getMD5Token(str(time.time())) + "-Android&version=1.6.5", key = b'neusofteducationplatform')
    f = s.get(login_url, headers=headers)
    f.raise_for_status()
    result = json.loads(f.text)
    if result["success"] == False:
        return -1, s
    return result, s
    
def get_province_code(user_province):
    provinces = {}
    provinces["北京市"] = "110000"
    provinces["天津市"] = "120000"
    provinces["河北省"] = "130000"
    provinces["山西省"] = "140000"
    provinces["内蒙古自治区"] = "150000"
    provinces["辽宁省"] = "210000"
    provinces["吉林省"] = "220000"
    provinces["黑龙江省"] = "230000"
    provinces["上海市"] = "310000"
    provinces["江苏省"] = "320000"
    provinces["浙江省"] = "330000"
    provinces["安徽省"] = "340000"
    provinces["福建省"] = "350000"
    provinces["江西省"] = "360000"
    provinces["山东省"] = "370000"
    provinces["河南省"] = "410000"
    provinces["湖北省"] = "420000"
    provinces["湖南省"] = "430000"
    provinces["广东省"] = "440000"
    provinces["广西壮族自治区"] = "450000"
    provinces["海南省"] = "460000"
    provinces["重庆市"] = "500000"
    provinces["四川省"] = "510000"
    provinces["贵州省"] = "520000"
    provinces["云南省"] = "530000"
    provinces["西藏自治区"] = "540000"
    provinces["陕西省"] = "610000"
    provinces["甘肃省"] = "620000"
    provinces["青海省"] = "630000"
    provinces["宁夏回族自治区"] = "640000"
    provinces["新疆维吾尔自治区"] = "650000"
    provinces["台湾省"] = "710000"
    provinces["香港特别行政区"] = "810000"
    provinces["澳门特别行政区"] = "820000"
    return provinces[user_province]


def renew(sess_id, session, user_id, user_name, user_province, home = 0) -> bool:
    #获取班级信息
    url = "http://e-report.neu.edu.cn/api/profiles/" + str(user_id) +"?xingming=" + urllib.parse.quote(str(user_name))
    f = session.get(url)
    f.raise_for_status()
    user_class = json.loads(f.text)["data"]["suoshubanji"]
    #获取credits，记录签到了多少天
    days = open("days", "r")
    credits = days.read()
    days.close()

    url = "http://e-report.neu.edu.cn/api/notes"

    #json参数拼接   
    data = {
        "_token": sess_id,
        "jibenxinxi_shifoubenrenshangbao": "1",
        "profile": {
            "xuegonghao": user_id,
            "xingming": user_name,
            "suoshubanji": user_class
            },
        "jiankangxinxi_muqianshentizhuangkuang":"正常",
        "xingchengxinxi_weizhishifouyoubianhua":"0",
        "cross_city":"无",
        "qitashixiang_qitaxuyaoshuomingdeshixiang":"",
        "credits": credits,
        "bmap_position": json.dumps({
            "accuracy": None,
            "altitude": None,
            "altitudeAccuracy": None,
            "heading": None,
            "latitude": ('41.65375230' if home == 0 else  MAP_LAT),
            "longitude": ('123.42235582' if home == 0 else MAP_LON),
            "speed": None,
            "timestamp": None,
            "point":{
                "lng": ('123.42235582' if home == 0 else MAP_LON),
                "lat": ('41.65375230' if home == 0 else MAP_LAT),
                "of": "inner"
            },
            "address":{
                "city": "",
                "city_code": 0,
                "district": "",
                "province":  ('辽宁省' if home == 0 else user_province),
                "street":"",
                "street_number": ""
            }
        }),
        "bmap_position_latitude": ('41.65375230' if home == 0 else MAP_LAT),
        "bmap_position_longitude": ('123.42235582' if home == 0 else MAP_LON),
        "bmap_position_address": ('辽宁省' if home == 0 else user_province),
        "bmap_position_status":"0",
        "ProvinceCode": ('210000' if home == 0 else get_province_code(user_province)),
        "CityCode": "",
        "travels": []
    }

    current_time = str(int(time.time() * 1000))
    headers = {
        "User-Agent":"Mozilla/5.0 (Linux; Android 11; KB2000 Build/RP1A.201005.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/87.0.4280.141 Mobile Safari/537.36",
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "tt": current_time,
        "neusoftapp": "neusoftAPP",
        "source": "neumobile",
        "idnumber": getDES3Token(str(USERNAME), key = b'neusoftneusoftneusoftneu'),
        "enp": getMD5Token(getSM3Token(str(PASSWORD)) + current_time)[5:28],
        "X-Requested-With": "com.sunyt.testdemo",
        "Referer": "http://e-report.neu.edu.cn/mobile/notes/create",
        "Origin": "http://e-report.neu.edu.cn",
        "Content-Type": "application/json;charset=utf-8",
        "X-XSRF-TOKEN": session.cookies["XSRF-TOKEN"]
    }
    f = session.post(url, headers=headers, data=json.dumps(data))
    f.raise_for_status()
    #print(f.status_code)
    if f.status_code != 201 and f.text.find("您的健康信息上报已成功") == -1:
        return False
    if int(credits) < 10:
        credits = str(int(credits) + 1)
    else:
        credits = str(10)
    days = open("days", "w")
    days.write(credits)
    days.close()

    return True
    
def get_token(s):
    current_time = str(int(time.time() * 1000))
    headers = {
        "User-Agent":"Mozilla/5.0 (Linux; Android 11; KB2000 Build/RP1A.201005.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/87.0.4280.141 Mobile Safari/537.36",
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "tt": current_time,
        "neusoftapp": "neusoftAPP",
        "source": "neumobile",
        "idnumber": getDES3Token(str(USERNAME), key = b'neusoftneusoftneusoftneu'),
        "enp": getMD5Token(getSM3Token(str(PASSWORD)) + current_time)[5:28],
        "X-Requested-With": "com.sunyt.testdemo",
        "Referer": "https://apipay.17wanxiao.com/"
    }
    f = s.get("http://e-report.neu.edu.cn/mobile/notes/create", headers=headers)
    f.raise_for_status()
    soup = BeautifulSoup(f.text, 'html.parser')
    if len(soup.select('input[name="_token"]')) != 1:
        return -1
    return soup.select('input[name="_token"]')[0]['value']
    


if __name__ == "__main__":
    if not USERNAME or not PASSWORD or not USER_PROVINCE or not MAP_LAT or not MAP_LON:
        print("参数出错，请无论如何也输入所有参数")
        exit(1)
    sleep_time = int(600 * random.random())
    print("延迟" + str(sleep_time) + "秒")
    time.sleep(sleep_time)
    print("登录中。。。。")
    user_detail, s = login(USERNAME, PASSWORD)
    if user_detail == -1:
        print("登录失败，请检查用户名和密码")
        exit(0)
    user_name = user_detail["message"]["USER_NAME"]
    print("登陆成功，正在签到。。。。")
    token = get_token(s)
    if token == -1:
        print("未知错误，请联系作者")
        exit(0)
    result = renew(token, s, USERNAME, user_name, USER_PROVINCE, HOME)
    if not result:
        print("未知错误，请联系作者")
        exit(0)
    print("签到成功，感谢使用")
    print('*' * 30)
