import requests
import base64
import random
import string
import re
import bs4
import hashlib
import datetime
import copy
import json

import threading

import queue
# import gevent
import multiprocessing
import logging
logging.basicConfig(filename='./log', format='%(asctime)s - %(levelname)s - %(threadName)s: %(message)s')
logging.root.setLevel(level=logging.INFO)
logger = logging.getLogger()


class sign():
    def __init__(self):
        self._appid = ''
        self._secret = ''
        self._temp_token = './temp_token'
        self._temp_jsapi = './temp_jsapi'
        import os
        if not os.path.exists(self._temp_token):
            self._temp_init()

    def _temp_init(self):
        with open(self._temp_token, "w+") as f:
            f.write(str({'token':'', 'time':'2019-01-01 00:00:00'}))
        with open(self._temp_jsapi, "w+") as f:
            f.write(str({'ticket':'', 'time':'2019-01-01 00:00:00'}))
    
    def _get_access_token(self):
        url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential'
        data = {
            'appid': self._appid,
            'secret': self._secret
        }
        res = requests.post(url=url, data=data).json()
        access_token = res['access_token']
        access_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        access_dict = {
            'token': access_token,
            'time': access_time
        }
        with open(self._temp_token, "w+") as wf:
            wf.write(str(access_dict))
        return access_token

    
    def _get_jsapi_ticket(self):
        jsapi_content = None
        with open(self._temp_jsapi, 'r') as f:
            jsapi_content = eval(f.read())
        
        old_ticket = jsapi_content['ticket']
        old_time = jsapi_content['time']

        old_time = datetime.datetime.strptime(old_time, "%Y-%m-%d %H:%M:%S")
        now_time = datetime.datetime.now()

        jsapi_ticket = None
        if (now_time - old_time).seconds <= 7200:
            jsapi_ticket = old_ticket
        else:
            token_content = None
            with open(self._temp_token, "r") as f:
                token_content = eval(f.read())
            
            old_token = token_content['token']
            old_time = token_content['time']

            old_time = datetime.datetime.strptime(old_time, "%Y-%m-%d %H:%M:%S")
            now_time = datetime.datetime.now()
            
            access_token = None

            if (now_time - old_time).seconds <= 7200:
                access_token = old_token
            else:
                access_token = self._get_access_token()

            res = requests.get('https://api.weixin.qq.com/cgi-bin/ticket/getticket?access_token={}&type=jsapi'.format(access_token)).json()
            
            jsapi_ticket = res['ticket']
            jsapi_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            jsapi_dict = {
                'ticket': jsapi_ticket,
                'time': jsapi_time
            }
            with open(self._temp_jsapi, "w+") as wf:
                wf.write(str(jsapi_dict))
        return jsapi_ticket

    def _get_random_nonceStr(self):
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(15))

    def _get_time_stamp(self):
        import time
        return int(time.time())

    def get_signature(self, url):
        import time
        ret = {
            'nonceStr': self._get_random_nonceStr(),
            'jsapi_ticket': self._get_jsapi_ticket(),
            'timestamp': self._get_time_stamp(),
            'url': url
        }
        string = '&'.join(['%s=%s' % (key.lower(), ret[key]) for key in sorted(ret)])
        ret['signature'] = hashlib.sha1(string.encode('utf-8')).hexdigest()
        ret['appid'] = self._appid
        return ret


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
        self._username = username
        self._password = password
        self._stuid = self._username
        self._grade = int(self._stuid[2])
        self._semester_num = 9 - self._grade
        self._timeout = 10
        self._headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Access-Control-Allow-Origin': '*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36'
        }
        self._session = requests.Session()
        self._cookies = None

    def _get(self, sess, *args, **kwargs):
        kwargs.update({'timeout': self._timeout})
        return sess.get(*args, **kwargs)

    def _post(self, sess, *args, **kwargs):
        kwargs.update({'timeout': self._timeout})
        return sess.post(*args, **kwargs)

    def login(self):
        from rsa import encrypt
        sess = self._session
        res = self._get(sess=sess, url='https://zjuam.zju.edu.cn/cas/v2/getPubKey', headers=self._headers).json()
        n, e = res['modulus'], res['exponent']
        encrypt_password = encrypt(n, e, self._password)
        res = self._get(sess=sess, url='https://zjuam.zju.edu.cn/cas/login?service=https://zuinfo.zju.edu.cn/system/login/login.zf')
        execution = re.search('name="execution" value=".*?"', res.text).group(0)[24:-1]
        data = {
            'username': self._username,
            'password': encrypt_password,
            'execution': execution,
            '_eventId': 'submit'
        }
        res = self._post(sess=sess, url='https://zjuam.zju.edu.cn/cas/login', data=data)
        status = re.search('class="login-page"', res.text)

        res = self._get(sess=sess, url='http://mapp.zju.edu.cn/lightapp/lightapp/getCardDetail').json()
        card = res['data']['query_card']['card'][0]
        self.phone = card['phone']
        self.cert = card['cert']
        self.name = card['name']
        self.account = card['account']
        self.gender = 'boy' if int(self.cert[-2]) % 2 else 'girl'
        return not status

    def go(self, res):
        t = []
        t.append(threading.Thread(target=zju._get_ecard,args=(self, res)))
        t.append(threading.Thread(target=zju._get_jwbinfosys,args=(self, res)))
        t.append(threading.Thread(target=zju._get_library,args=(self, res)))
        t.append(threading.Thread(target=zju._get_cc98,args=(self, res)))
        t.append(threading.Thread(target=zju._get_sport,args=(self, res)))
        try:
            for i in t:
                i.start()
            for i in t:
                i.join()
        except Exception as e:
            raise e

    def retry(times):
        def outer_wrapper(func):
            def inner_wrapper(self, *arg, **kwargs):
                for i in range(times):
                    try:
                        starttime = datetime.datetime.now()
                        ret = func(self, *arg, **kwargs)
                        endtime = datetime.datetime.now()
                        logger.info("func: {} time: {}s username: {}".format(func.__name__, (endtime - starttime).seconds, self._username))
                        # if no error, just break
                        break
                    except Exception as e:
                        continue
            return inner_wrapper
        return outer_wrapper


    def _get_ecard_part(self, sess, start_page, end_page, q):
        # from gevent import monkey; monkey.patch_all()
        ecard_biggest = {
            'occtime': '',
            'mercname': '',
            'tranamt': 0.0
        }
        ecard_day = {}
        ecard_shower = 0
        ecard_market = 0
        ecard_normal = 0
        ecard_bank = 0
        ecard_merc = {}

        for i in range(start_page, end_page):
            params = {
                'curpage': '{}'.format(i),
                'pagesize': '50',
                'account': '{}'.format(self.account),
                'queryStart': '20150820',
                'queryEnd': '20190302'
            }
            res = self._get(sess=sess, url='http://mapp.zju.edu.cn/lightapp/lightapp/getHistoryConsumption', params=params).json()
            items = res['data']['query_his_total']['total']
            for item in items:
                # 20190120105050
                occtime = item['occtime']
                tranamt = int(item['sign_tranamt']) / 100.0
                tranname = item['tranname']
                mercname = item['mercname']
                trancode = item['trancode']
                if tranamt < 0 and tranamt < ecard_biggest['tranamt']:
                    ecard_biggest['occtime'] = occtime
                    ecard_biggest['mercname'] = mercname
                    ecard_biggest['tranamt'] = tranamt
                if tranamt < 0:
                    daytime = occtime[:8]
                    if daytime not in ecard_day.keys():
                        ecard_day[daytime] = 0
                    else:
                        ecard_day[daytime] += -1 * tranamt
                if trancode == '15':
                    if mercname.find('水控') != -1:
                        ecard_shower += 1
                    else:
                        ecard_market += 1
                if trancode == '16':
                    ecard_bank += 1
                if trancode == '94':
                    ecard_normal += 1
                if mercname not in ecard_merc.keys():
                    ecard_merc[mercname] = 1
                else:
                    ecard_merc[mercname] += 1
        q.put((ecard_biggest, ecard_day, ecard_shower, ecard_market, ecard_normal, ecard_bank, ecard_merc))
            


    @retry(2)
    def _get_ecard(self, response):
        sess = copy.deepcopy(self._session)
        i = 1

        params = {
                'curpage': '{}'.format(i),
                'pagesize': '50',
                'account': '{}'.format(self.account),
                'queryStart': '20150820',
                'queryEnd': '20190221'
            }
        res = self._get(sess=sess, url='http://mapp.zju.edu.cn/lightapp/lightapp/getHistoryConsumption', params=params).json()
        # 1 pages
        pages = int(int(res['data']['query_his_total']['rowcount']) / int(res['data']['query_his_total']['pagesize']))
        
        middle = int(pages / 2)


        ecard_biggest = {
            'occtime': '',
            'mercname': '',
            'tranamt': 0.0
        }
        ecard_day = {}
        ecard_shower = 0
        ecard_market = 0
        ecard_normal = 0
        ecard_bank = 0
        ecard_merc = {}


        t = []
        
        q = queue.Queue()
        t.append(threading.Thread(target=zju._get_ecard_part,args=(self, sess, 1, int(pages/3), q)))
        t.append(threading.Thread(target=zju._get_ecard_part,args=(self, sess, int(pages/3), int(pages/3*2), q)))
        t.append(threading.Thread(target=zju._get_ecard_part,args=(self, sess, int(pages/3*2), pages+2, q)))
        try:
            for i in t:
                i.start()
            for i in t:
                i.join()
        except Exception as e:
            raise e

        while not q.empty():
            ecard_biggest_t, ecard_day_t, ecard_shower_t, ecard_market_t, ecard_normal_t, ecard_bank_t, ecard_merc_t =  q.get()
            ecard_biggest = ecard_biggest_t if ecard_biggest_t['tranamt'] < ecard_biggest['tranamt'] else ecard_biggest
            ecard_day.update(ecard_day_t)
            ecard_shower += ecard_shower_t
            ecard_normal += ecard_normal_t
            ecard_market += ecard_market_t
            ecard_bank += ecard_bank_t
            for key, value in ecard_merc_t.items():
                if key not in ecard_merc.keys():
                    ecard_merc[key] = value
                else:
                    ecard_merc[key] += value

        ecard = {}

        ecard_merc_list = sorted(ecard_merc.items(), key=lambda d:d[1], reverse=True)
        ecard_most = [{'mercname': i[0], 'count': i[1]} for i in ecard_merc_list[:3]]

        occtime = ecard_biggest['occtime']
        ecard_biggest['occtime'] = '{}-{}-{} {}:{}:{}'.format(occtime[0:4], occtime[4:6], occtime[6:8], occtime[8:10], occtime[10:12], occtime[12:14])
        ecard_biggest['tranamt'] = -1 * ecard_biggest['tranamt']

        ecard_day = sorted(ecard_day.items(), key=lambda d:d[1], reverse=True)
        ecard['day'] = {
            'time': '{}-{}-{}'.format(ecard_day[0][0][0:4], ecard_day[0][0][4:6], ecard_day[0][0][6:8]),
            'count': ecard_day[0][1]
        }
        ecard['merc'] = ecard_merc_list
        ecard['shower'] = ecard_shower
        ecard['bank'] = ecard_bank
        ecard['normal'] = ecard_normal
        ecard['market'] = ecard_market
        ecard['biggest'] = ecard_biggest
        ecard['most'] = ecard_most
        ecard['total'] = len(ecard_merc_list)
        response['ecard'] = ecard

    def _get_jwbinfosys_util(self, res, teacher2num, semester2num, teacher2course, slug):
        soup = bs4.BeautifulSoup(res.text, 'html.parser')
        year = soup.find(id='xnd').find(attrs={'selected': "selected"}).text
        table = soup.find(id='xsgrid')
        trs = table.findAll('tr')[1:]
        for tr in trs:
            tds = tr.findAll('td')
            course_id, course_name, teacher, semester = tds[0].text, tds[1].text, tds[2].text, tds[3].text
            teachers = teacher.split('<br/>')
            for teacher in teachers:
                if teacher not in teacher2course.keys():
                    teacher2course[teacher] = [course_name]
                else:
                    teacher2course[teacher].append(course_name)
                
                if teacher not in teacher2num.keys():
                    teacher2num[teacher] = 1
                else:
                    teacher2num[teacher] += 1
        # 2015-2016 13s
        semester2num[slug] = len(trs)

    def _get_jwbinfosys_course(self, sess, semester_num=4):
        base = 2018
        teacher2num = {}
        semester2num = {}
        teacher2course = {}
        res = None

        res = self._get(sess=sess, url='http://jwbinfosys.zju.edu.cn/xskbcx.aspx?xh={}'.format(self._stuid))
        self._get_jwbinfosys_util(res, teacher2num, semester2num, teacher2course, '2018-2019 春夏')
        viewstate = re.search(
            'name="__VIEWSTATE" value=".*?"', res.text).group(0)[26:-1]
        data = {
            '__VIEWSTATE': viewstate,
            'xnd': '2018-2019',
            'xqd': '1|秋、冬'.encode('GBK')
        }
        res = self._post(sess=sess, url='http://jwbinfosys.zju.edu.cn/xskbcx.aspx?xh={}'.format(self._stuid), data=data)
        self._get_jwbinfosys_util(res, teacher2num, semester2num, teacher2course, '2018-2019 秋冬')

        for i in range(1, self._semester_num):
            viewstate = re.search(
                'name="__VIEWSTATE" value=".*?"', res.text).group(0)[26:-1]
            data = {
                '__VIEWSTATE': viewstate,
                'xnd': '{}-{}'.format(base-i, base-i+1),
            }
            res = self._post(sess=sess, 
                url='http://jwbinfosys.zju.edu.cn/xskbcx.aspx?xh={}'.format(self._stuid), data=data)
            self._get_jwbinfosys_util(res, teacher2num, semester2num, teacher2course, '{}-{} 春夏'.format(base-i, base-i+1))

            viewstate = re.search(
                'name="__VIEWSTATE" value=".*?"', res.text).group(0)[26:-1]
            data = {
                '__VIEWSTATE': viewstate,
                'xnd': '{}-{}'.format(base-i, base-i+1),
                'xqd': '1|秋、冬'.encode('GBK')
            }
            res = self._post(sess=sess, 
                url='http://jwbinfosys.zju.edu.cn/xskbcx.aspx?xh={}'.format(self._stuid), data=data)
            self._get_jwbinfosys_util(res, teacher2num, semester2num, teacher2course, '{}-{} 秋冬'.format(base-i, base-i+1))


        soup = bs4.BeautifulSoup(res.text, 'html.parser')
        year = soup.find(id='xnd').find(attrs={'selected': "selected"}).text
        table = soup.find(id='xsgrid')
        trs = table.findAll('tr')[1:]
        first_semester_course = []
        for tr in trs:
            tds = tr.findAll('td')
            course_name, teacher, semester, time, place = tds[1].text, tds[2].text, tds[3].text, tds[4].text, tds[5].text
            if semester.find('秋') != -1:
                places = place.split('<br/>')
                times = time.split('<br/>')
                time, place = None, None
                if len(times) >= 2: 
                    time = sorted(times)[0]
                    place = places[times.index(time)]
                else:
                    place = places[0]
                    time = times[0]
                first_semester_course.append((course_name, teacher, place, time))

        first_semester_course = sorted(first_semester_course, key=lambda d:d[-1])
        first_course = None
        if first_semester_course[0][0] == '军训':
            first_course = {
                'name': first_semester_course[1][0],
                'teacher': first_semester_course[1][1],
                'place': first_semester_course[1][2]
            }
        else:
            first_course = {
                'name': first_semester_course[0][0],
                'teacher': first_semester_course[0][1],
                'place': first_semester_course[0][2]
            }
        return teacher2num, teacher2course, semester2num, first_course

    @retry(2)
    def _get_jwbinfosys(self, response):
        # ajax
        # get base cookie
        sess = copy.deepcopy(self._session)
        jwbinfosys = {}
        self._get(sess=sess, url='http://jwbinfosys.zju.edu.cn/default2.aspx')
        res = self._get(sess=sess, url='http://jwbinfosys.zju.edu.cn/xscj.aspx?xh={}'.format(self._stuid))
        # constant
        viewstate = re.search(
            'name="__VIEWSTATE" value=".*?"', res.text).group(0)[26:-1]
        data = {
            '__VIEWSTATE': viewstate,
            'Button2': '在校成绩查询'.encode('GBK')
        }

        res = self._get(sess=sess, url='http://jwbinfosys.zju.edu.cn/xscj_zg.aspx?xh={}'.format(self._stuid))
        tds = re.findall('<tr[\S\s]*?</tr>', res.text)[1:]
        jwbinfosys['major_count'] = len(tds)
         
        res = self._post(sess=sess, url='http://jwbinfosys.zju.edu.cn/xscj.aspx?xh={}'.format(self._stuid), data=data)
        tds = re.findall('<tr[\S\s]*?</tr>', res.text)[1:]
        
        course2score = {}
        total_credit = 0
        sport2num = {}
        for td in tds:
            infos = re.findall('<td>[\S\s]*?</td>', td)
            infos = [i.replace('<td>', '').replace('</td>', '') for i in infos]
            course_info, course_name, score, credit, gp = infos[:5]
            if float(gp) >= 1.5:
                total_credit += float(credit)
            course_time = course_info[1:12]
            course_id = course_info[14:22]
            if course_id[:3] == '401':
                index = course_name.find('（')
                course_type = course_name if index == -1 else course_name[:index]
                if course_type not in sport2num.keys():
                    sport2num[course_type] = 1
                else:
                    sport2num[course_type] += 1
            # score may be '合格'
            try:
                if int(score):
                    course2score[course_name] = int(score)
            except Exception as e:
                continue
        jwbinfosys['sport_count'] = len(sport2num)
        jwbinfosys['total_credit'] = total_credit
        jwbinfosys['total_count'] = len(tds)
        course2score = sorted(course2score.items(), key=lambda d:d[1],reverse=True)
        
        jwbinfosys['score'] = [{'name': i[0], 'count': i[1]} for i in course2score[:3]]

        teacher2num, teacher2course, semester2num, first_course = self._get_jwbinfosys_course(sess=sess)
        
        jwbinfosys['first_course'] = first_course
        # the teacher with most courses
        teacher2num = sorted(teacher2num.items(), key=lambda d:d[1],reverse=True)
        jwbinfosys['teacher'] = {
            'name': teacher2num[0][0],
            'count': teacher2num[0][1],
            'course': teacher2course[teacher2num[0][0]]
        }
        semester2num = sorted(semester2num.items(), key=lambda d:d[1],reverse=True)
        jwbinfosys['semester'] = {
            'name': semester2num[0][0],
            'count': semester2num[0][1],
            'avg': int(sum([i[1] for i in semester2num]) / len(semester2num))
        }
        response['jwbinfosys'] = jwbinfosys

    def _get_library_util(self, date):
        date1 = datetime.datetime.strptime(date, '%Y%m%d')
        delta = datetime.timedelta(days=-40)
        date2 = date1 + delta
        return date2.strftime('%Y-%m-%d')

    def _get_library_topic(self, sess, start, end, topic_urls, q):
        topic2num = {}
        for i in range(start, end):
            topic_url = topic_urls[i]
            res = self._get(sess=sess, url=topic_url)
            res.encoding = 'utf-8'
            soup = bs4.BeautifulSoup(res.text, 'html.parser')
            table = soup.findAll('table')[-2]
            trs = table.findAll('tr')[1:]
            for tr in trs:
                tds = tr.findAll('td')
                for i in range(0, len(tds)):
                    if (tds[i].text).find('主题') != -1:
                        try:
                            for topic in ("".join(tds[i+1].text.strip('\n').split())).split('-'):
                                if topic not in topic2num.keys():
                                    topic2num[topic] = 1
                                else:
                                    topic2num[topic] += 1
                            break
                        except Exception as e:
                            break
        q.put((topic2num))

    @retry(2)
    def _get_library(self, response):
        # ISO-8859-1
        sess = copy.deepcopy(self._session)
        res = self._get(sess=sess, url='http://webpac.zju.edu.cn/zjusso')
        res.encoding = 'utf-8'
        # ?
        a = re.search('<a href=.*?func=bor-history-loan.*?</a>', res.text).group(0)
        href = re.search('\(.*?\)', a).group(0)[2:-2]
        res = self._get(sess=sess, url=href)
        res.encoding = 'utf-8'
        soup = bs4.BeautifulSoup(res.text, 'html.parser')
        table = soup.findAll('table')[-1]
        trs = table.findAll('tr')[1:]

        library = {}
        book_info = []
        topic_urls = []
        author2num, place2num, topic2num = {}, {}, {}
        try:
            for tr in trs:
                tds = tr.findAll('td')
                author, book_name, date, place = tds[1].text.strip(',').strip('，'), tds[2].text, tds[4].text, tds[-1].text
                book_info.append((author, book_name, date))

                if place not in place2num.keys():
                    place2num[place] = 1
                else:
                    place2num[place] += 1

                if author not in author2num.keys():
                    author2num[author] = 1
                else:
                    author2num[author] += 1

                # topic
                topic_url = tds[2].find('a')['href']
                topic_urls.append(topic_url)
                # res = self._get(sess=sess, url=topic_url)
                # res.encoding = 'utf-8'
                # soup = bs4.BeautifulSoup(res.text, 'html.parser')
                # table = soup.findAll('table')[-2]
                # trs = table.findAll('tr')[1:]
                # for tr in trs:
                #     tds = tr.findAll('td')
                #     for i in range(0, len(tds)):
                #         if (tds[i].text).find('主题') != -1:
                #             try:
                #                 for topic in ("".join(tds[i+1].text.strip('\n').split())).split('-'):
                #                     if topic not in topic2num.keys():
                #                         topic2num[topic] = 1
                #                     else:
                #                         topic2num[topic] += 1
                #                 break
                #             except Exception as e:
                #                 break
                    
            first_book = {
                'author': book_info[-1][0],
                'name': book_info[-1][1],
                'date': self._get_library_util(book_info[-1][2])
            }

            last_book = {
                'author': book_info[0][0],
                'name': book_info[0][1],
                'date': self._get_library_util(book_info[0][2])
            }
        except Exception as e:
            library['total_count'] = 0
            response['library'] = library
            return
        

        t = []
        items = len(topic_urls)
        q = queue.Queue()
        
        seeds = 8
        indexs = [int(items/(seeds/i)) if i else 0 for i in range(0, seeds+1)]
        for i in range(seeds):
            t.append(threading.Thread(target=zju._get_library_topic, args=(self, sess, indexs[i], indexs[i+1], topic_urls, q)))
        try:
            for i in t:
                i.start()
            for i in t:
                i.join()
        except Exception as e:
            raise e

        while not q.empty():
            topic2num_t =  q.get()
            for key, value in topic2num_t.items():
                if key not in topic2num.keys():
                    topic2num[key] = value
                else:
                    topic2num[key] += value


        topic2num = sorted(topic2num.items(), key=lambda d:d[1] ,reverse=True)
        place2num = sorted(place2num.items(), key=lambda d:d[1],reverse=True)
        author2num = sorted(author2num.items(), key=lambda d:d[1],reverse=True)

        library['total_count'] = len(book_info)
        library['author'] = {
            'name': author2num[0][0],
            'count': author2num[0][1]
        }
        library['first_book'] = first_book
        library['last_book'] = last_book
        library['place'] = {
            'count': len(place2num),
            'most_name': place2num[0][0]
        }
        library['topic'] = [i[0] for i in topic2num[:6]]
        response['library'] = library


    def _get_cc98_util(self, sess, title, q):
        post_count = 0
        follow_count = 0
        fan_count = 0
        register_time = "0000-00-00"
        name = title.text.strip().strip('\n').strip()
        res = self._get(sess=sess, url="https://api.cc98.org/user/name/{}".format(name)).json()
        post_count += int(res['postCount'])
        follow_count += int(res['followCount'])
        fan_count += int(res['fanCount'])
        register_time = res['registerTime'][:10]
        q.put((post_count, follow_count, fan_count, register_time))


    @retry(2)
    def _get_cc98(self, response):
        sess = copy.deepcopy(self._session)

        res = self._get(sess=sess, url='https://account.cc98.org/My')
        soup = bs4.BeautifulSoup(res.text, 'html.parser')
        tables = soup.findAll(attrs={'class': "table table-sm"})
        titles = soup.findAll(attrs={'class': "card-title"})
        cc98 = {}
        cc98['gender'] = self.gender
        cc98['count'] = len(tables)
        cc98['login_times'] = 0
        cc98['comment_times'] = 0
        cc98['post_count'] = 0
        cc98['follow_count'] = 0
        cc98['fan_count'] = 0
        cc98['register_time'] = "2020-01-01"
        for table in tables:
            trs = table.findAll('tr')
            infos = []
            for tr in trs:
                tds = tr.findAll('td')
                infos.append(tds[1].text)
            register_time, last_login, login_times, comment_times = infos[0], infos[1], infos[2], infos[3]
            cc98['login_times'] += int(login_times)
            cc98['comment_times'] += int(comment_times)

        t = []
        
        q = queue.Queue()
        for title in titles:
            t.append(threading.Thread(target=zju._get_cc98_util,args=(self, sess, title, q)))
        try:
            for i in t:
                i.start()
            for i in t:
                i.join()
        except Exception as e:
            raise e

        while not q.empty():
            post_count, follow_count, fan_count, register_time =  q.get()
            cc98['post_count'] += post_count
            cc98['follow_count'] += follow_count
            cc98['fan_count'] += fan_count
            cc98['register_time'] = register_time if register_time < cc98['register_time'] else cc98['register_time']

        response['cc98'] =  cc98

    @retry(2)
    def _get_sport(self, response):
        sess = copy.deepcopy(self._session)
        data = {
            'type': 'base_pft',
            'username': self._username,
            'password': self._password
        }

        res = self._post(sess=sess, url='http://www.tyys.zju.edu.cn/ggtypt/dologin', data=data)
        res = self._get(sess=sess, url='http://www.tyys.zju.edu.cn/pft/myresult')

        soup = bs4.BeautifulSoup(res.text, 'html.parser')
        table = soup.find(id='dataTables-main')
        tbody = table.find('tbody')
        trs = tbody.findAll('tr')

        years, heights, weights, bmis, scores, runs = [], [], [], [], [], []
        for tr in trs:
            tds = tr.findAll('td')
            tds = [i.text.strip() for i in tds]
            if tds[-1] == '免测' or tds[-1] == '暂无':
                continue
            else:
                score = float(tds[-1]) 
            year, bmi, height, weight, run = tds[0], tds[2], tds[3], tds[4], tds[9].split('/')[0].replace('.', "'")
            # format: 2018-2019学年
            year = '{}-{}'.format(year[2:4], year[7:9])
            years.append(year)
            heights.append(height)
            weights.append(weight)
            scores.append(score)
            runs.append(run)
            bmis.append(bmi)
        years = years[::-1]
        heights = heights[::-1]
        weights = weights[::-1]
        bmis = bmis[::-1]
        runs = runs[::-1]
        sport = {}
        sport['height'] = heights
        sport['weight'] = weights
        sport['year'] = years
        sport['score'] = max(scores)
        sport['bmi'] = bmis
        sport['run'] = runs
        response['sport'] =  sport
