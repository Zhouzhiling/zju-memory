import requests
import base64
import random
import re
import pymysql
import bs4


class zju():
    def __init__(self):
        self._config_path = './config.json'
        self._config = None
        with open(self._config_path, "r", encoding='utf-8') as f:
            self._config = eval(f.read())

        self.username = self._config['username']
        self.password = self._config['password']
        self.stuid = self.username

        self._headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36'
        }

        self._conn = pymysql.connect(
            host="localhost",
            user="root",
            password="c86461112",
            database="zju"
        )

        self._cursor = self._conn.cursor()

        self._session = requests.Session()

        self._cookies = None

    # def login_myzju(self):
    #     url = 'http://my.zju.edu.cn/_web/portal/casLogin.jsp?_p=YXM9MSZwPTEmbT1OJg__'
    #     username = self.username
    #     password_encrypt = base64.b64encode(self.password.encode('utf-8'))
    #     data = {
    #         'casLoginUrl': 'https://zjuam.zju.edu.cn/cas/login?service=http://my.zju.edu.cn/_web/fusionportal/index.jsp?_p=YXM9MSZwPTEmbT1OJg__',
    #         'userName': username,
    #         'password': password_encrypt
    #     }
    #     res = self.session.post(
    #         url=url, data=data, headers=self.__headers).json()

    def sql(self, sql):
        try:
            self._cursor.execute(sql)
            self._conn.commit()
        except:
            self._conn.rollback()

    def login(self):
        from rsa import encrypt
        res = self._session.get(
            url='https://zjuam.zju.edu.cn/cas/v2/getPubKey', headers=self._headers).json()
        n, e = res['modulus'], res['exponent']
        encrypt_password = encrypt(n, e, self.password)
        res = self._session.get(
            url='https://zjuam.zju.edu.cn/cas/login?service=https://zuinfo.zju.edu.cn/system/login/login.zf')
        execution = re.search(
            'name="execution" value=".*?"', res.text).group(0)[24:-1]
        data = {
            'username': self.username,
            'password': encrypt_password,
            'execution': execution,
            '_eventId': 'submit'
        }
        self._session.post(url='https://zjuam.zju.edu.cn/cas/login', data=data)

        # TODO
        sql = "INSERT INTO `account` (`username`, `password`) VALUES ('{}', '{}')".format(
            self.username, self.password)
        self.sql(sql)
        self._cookies = self._session.cookies

    def get_grade(self):
        # ajax
        # get base cookie
        self._session.get(url='http://jwbinfosys.zju.edu.cn/default2.aspx')
        res = self._session.get(
            url='http://jwbinfosys.zju.edu.cn/xscj.aspx?xh={}'.format(self.stuid))
        # constant
        viewstate = re.search(
            'name="__VIEWSTATE" value=".*?"', res.text).group(0)[26:-1]
        data = {
            '__VIEWSTATE': viewstate,
            'Button2': '在校成绩查询'.encode('GBK')
        }

        major_course_id = []
        res = self._session.get(
            url='http://jwbinfosys.zju.edu.cn/xscj_zg.aspx?xh={}'.format(self.stuid))
        tds = re.findall('<tr[\S\s]*?</tr>', res.text)[1:]
        for td in tds:
            infos = re.findall('<td>[\S\s]*?</td>', td)
            infos = [i.replace('<td>', '').replace('</td>', '') for i in infos]
            course_info, course_name, score, credit, gp = infos[:5]
            course_id = course_info[14:22]
            major_course_id.append(course_id)

        res = self._session.post(
            url='http://jwbinfosys.zju.edu.cn/xscj.aspx?xh={}'.format(self.stuid), data=data)
        tds = re.findall('<tr[\S\s]*?</tr>', res.text)[1:]
        for td in tds:
            infos = re.findall('<td>[\S\s]*?</td>', td)
            infos = [i.replace('<td>', '').replace('</td>', '') for i in infos]
            course_info, course_name, score, credit, gp = infos[:5]
            course_time = course_info[1:12]
            course_id = course_info[14:22]
            if course_id in major_course_id:
                sql = "INSERT INTO `grade` (`username`, `course_id`, `course_name`, `course_time`, `score`, `credit`, `gp`, `major`) " \
                    "VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '1')".format(
                        self.username, course_id, course_name, course_time, score, float(credit), float(gp))
            else:
                sql = "INSERT INTO `grade` (`username`, `course_id`, `course_name`, `course_time`, `score`, `credit`, `gp`, `major`) " \
                    "VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '0')".format(
                        self.username, course_id, course_name, course_time, score, float(credit), float(gp))
            self.sql(sql)

    def _course_sql(self, res):
        soup = bs4.BeautifulSoup(res.text, 'html.parser')
        year = soup.find(id='xnd').find(attrs={'selected': "selected"}).text
        table = soup.find(id='xsgrid')
        trs = table.findAll('tr')[1:]
        for tr in trs:
            tds = tr.findAll('td')
            course_id, course_name, teacher, semester = tds[0].text, tds[1].text, tds[2].text, tds[3].text
            sql = "INSERT INTO `course` (`username`, `course_id`, `course_name`, `teacher`, `year`, `semester`) " \
                "VALUES ('{}', '{}', '{}', '{}', '{}', '{}')".format(
                    self.stuid, course_id, course_name, teacher, year, semester)
            self.sql(sql)

    def get_course(self):
        self._session.get(url='http://jwbinfosys.zju.edu.cn/default2.aspx')
        res = self._session.get(
            url='http://jwbinfosys.zju.edu.cn/xskbcx.aspx?xh={}'.format(self.stuid))
        self._course_sql(res)

        viewstate = re.search(
            'name="__VIEWSTATE" value=".*?"', res.text).group(0)[26:-1]
        data = {
            '__VIEWSTATE': viewstate,
            'xnd': '2018-2019',
            'xqd': '1|秋、冬'.encode('GBK')
        }
        res = self._session.post(
            url='http://jwbinfosys.zju.edu.cn/xskbcx.aspx?xh={}'.format(self.stuid), data=data)
        self._course_sql(res)

        viewstate = re.search(
            'name="__VIEWSTATE" value=".*?"', res.text).group(0)[26:-1]
        data = {
            '__VIEWSTATE': viewstate,
            'xnd': '2017-2018',
        }
        res = self._session.post(
            url='http://jwbinfosys.zju.edu.cn/xskbcx.aspx?xh={}'.format(self.stuid), data=data)
        self._course_sql(res)

        viewstate = re.search(
            'name="__VIEWSTATE" value=".*?"', res.text).group(0)[26:-1]
        data = {
            '__VIEWSTATE': viewstate,
            'xnd': '2017-2018',
            'xqd': '1|秋、冬'.encode('GBK')
        }
        res = self._session.post(
            url='http://jwbinfosys.zju.edu.cn/xskbcx.aspx?xh={}'.format(self.stuid), data=data)
        self._course_sql(res)

        viewstate = re.search(
            'name="__VIEWSTATE" value=".*?"', res.text).group(0)[26:-1]
        data = {
            '__VIEWSTATE': viewstate,
            'xnd': '2016-2017',
        }
        res = self._session.post(
            url='http://jwbinfosys.zju.edu.cn/xskbcx.aspx?xh={}'.format(self.stuid), data=data)
        self._course_sql(res)

        viewstate = re.search(
            'name="__VIEWSTATE" value=".*?"', res.text).group(0)[26:-1]
        data = {
            '__VIEWSTATE': viewstate,
            'xnd': '2016-2017',
            'xqd': '1|秋、冬'.encode('GBK')
        }
        res = self._session.post(
            url='http://jwbinfosys.zju.edu.cn/xskbcx.aspx?xh={}'.format(self.stuid), data=data)
        self._course_sql(res)

        viewstate = re.search(
            'name="__VIEWSTATE" value=".*?"', res.text).group(0)[26:-1]
        data = {
            '__VIEWSTATE': viewstate,
            'xnd': '2015-2016',
        }
        res = self._session.post(
            url='http://jwbinfosys.zju.edu.cn/xskbcx.aspx?xh={}'.format(self.stuid), data=data)
        self._course_sql(res)

        viewstate = re.search(
            'name="__VIEWSTATE" value=".*?"', res.text).group(0)[26:-1]
        data = {
            '__VIEWSTATE': viewstate,
            'xnd': '2015-2016',
            'xqd': '1|秋、冬'.encode('GBK')
        }
        res = self._session.post(
            url='http://jwbinfosys.zju.edu.cn/xskbcx.aspx?xh={}'.format(self.stuid), data=data)
        self._course_sql(res)

    def get_exam(self):
        self._session.get(url='http://jwbinfosys.zju.edu.cn/default2.aspx')
        res = self._session.get(
            url='http://jwbinfosys.zju.edu.cn/xskscx.aspx?xh={}'.format(self.stuid))
        pass

    def get_ecard(self):
        merc = {}
        res = self._session.get(
            url='http://mapp.zju.edu.cn/lightapp/lightapp/getCardDetail').json()
        card = res['data']["query_card"]['card'][0]
        self.name = card['name']
        self.account = card['account']
        i = 1
        while True:
            params = {
                'curpage': '{}'.format(i),
                'pagesize': '10',
                'account': '{}'.format(self.account),
                'queryStart': '20150820',
                'queryEnd': '20190221'
            }
            res = self._session.get(
                url='http://mapp.zju.edu.cn/lightapp/lightapp/getHistoryConsumption', params=params).json()
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
                print(occtime, tranamt, mercname)
                # sql = "INSERT INTO `ecard` (`username`, `occtime`, `tranamt`, `mercname`) VALUES ('{}', '{}', '{}', '{}')".format(
                #     self.username, occtime, tranamt, mercname)
                # self.sql(sql)

            nextpage = int(res['data']['query_his_total']['nextpage'])
            if not nextpage:
                break
            i += 1
        print(merc)

    def get_cc98_account(self):
        res = self._session.get('https://account.cc98.org/My')
        soup = bs4.BeautifulSoup(res.text, 'html.parser')
        table = soup.find(attrs={'class': "table table-sm"})
        trs = table.findAll('tr')
        infos = []
        for tr in trs:
            tds = tr.findAll('td')
            infos.append(tds[1].text)
        register_time, last_login, login_times, comment_times = infos[0], infos[1], infos[2], infos[3]

    def get_library(self):
        res = self._session.get('http://webpac.zju.edu.cn/zjusso')
        soup = bs4.BeautifulSoup(res.text, 'html.parser')
        table = soup.find(attrs={'class': "indent1"})
        trs = table.findAll('tr')
        for tr in trs:
            tds = tr.findAll('td')
            text, count = tds[0].text, tds[1].text
            print(text, count)



if __name__ == '__main__':
    obj = zju()
    obj.login()
    obj.get_ecard()
    # print(obj.username)
