import requests
import base64
import random
import re
import pymysql
import bs4

import threading

def pool_lock(func):
    def wrapper(*arg, **kwargs):
        with pool._instance_lock:
            return func(*arg, **kwargs)
    return wrapper


class pool():
    _instance_lock = threading.Lock()
    _max_size = 100
    _obj_pool = {}
    def __new__(cls, *args, **kwargs):
        if not hasattr(pool, "_instance"):
            with pool._instance_lock:
                if not hasattr(pool, "_instance"):
                    pool._instance = object.__new__(cls)
        return pool._instance

    def __init__(self):
        pass
    
    @pool_lock
    def save(self, id, obj):
        pool._obj_pool[id] = obj

    @pool_lock
    def get(self, id):
        return pool._obj_pool[id]

    @pool_lock
    def delete(self, id):
        pool._obj_pool.pop(id)

    @pool_lock
    def clear(self):
        pool._obj_pool.clear()

    @pool_lock
    def keys(self):
        return list(pool._obj_pool.keys())

    @pool_lock
    def exists(self, username):
        return username in pool._obj_pool.keys()

    @pool_lock
    def empty(self):
        return not len(pool._obj_pool)


class zju():
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.stuid = self.username
        self._headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36'
        }
        self._session = requests.Session()
        self._cookies = None

    def login(self):
        from rsa import encrypt
        res = self._session.get(url='https://zjuam.zju.edu.cn/cas/v2/getPubKey', headers=self._headers).json()
        n, e = res['modulus'], res['exponent']
        encrypt_password = encrypt(n, e, self.password)
        res = self._session.get(url='https://zjuam.zju.edu.cn/cas/login?service=https://zuinfo.zju.edu.cn/system/login/login.zf')
        execution = re.search('name="execution" value=".*?"', res.text).group(0)[24:-1]
        data = {
            'username': self.username,
            'password': encrypt_password,
            'execution': execution,
            '_eventId': 'submit'
        }
        res = self._session.post(url='https://zjuam.zju.edu.cn/cas/login', data=data)
        status = re.search('class="login-page"', res.text)
        return not status

    def get_ecard(self):
        merc = {}
        res = self._session.get(url='http://mapp.zju.edu.cn/lightapp/lightapp/getCardDetail').json()
        card = res['data']["query_card"]['card'][0]
        self.name = card['name']
        self.account = card['account']
        i = 1
        while True:
            params = {
                'curpage': '{}'.format(i),
                'pagesize': '50',
                'account': '{}'.format(self.account),
                'queryStart': '20150820',
                'queryEnd': '20190221'
            }
            res = self._session.get(url='http://mapp.zju.edu.cn/lightapp/lightapp/getHistoryConsumption', params=params).json()
            items = res['data']['query_his_total']['total']
            for item in items:
                occtime = item['occtime']
                tranamt = int(item['sign_tranamt']) / 100.0
                tranname = item['tranname']
                mercname = item['mercname']
                if mercname not in merc.keys():
                    merc[mercname] = 1
                else:
                    merc[mercname] += 1
            nextpage = int(res['data']['query_his_total']['nextpage'])
            if not nextpage:
                break
            i += 1
        res = []
        for key, value in merc.items():
            res.append([key, value])
        print(res)
        return res
    
    