"""
@Coding:utf-8
@Author:hbc
@Time:2022/9/2 10:09
@File:auto_punch_notify
@Software:PyCharm
"""
import yagmail
import urllib.parse
import urllib.request


class Notify:
    def __init__(self, logger=None, time=None):
        self.logging = logger
        self.time = time

    def send_by_email(self, data):
        try:
            # 连接发信服务
            yag = yagmail.SMTP(user="cloud-notify@qq.com", password="cpllbrxsbejreadi", host='smtp.qq.com', port=465)
            self.out_logger(yag)
            # 邮箱正文模板
            contents = ['打卡状态：%s<br>' % data['result'], '打卡时间：%s<br>' % data['time'], '打卡地址：%s' % data['addr']]
            self.out_logger(contents)
            if data is None or "receive_email" not in data or data['receive_email'] is None:
                yag.send("752484360@qq.com", "Test", contents)
            else:
                yag.send(data['receive_email'], data['title'], contents)
        except Exception:
            raise

    def send_by_phone(self, data):
        try:
            # 接口地址
            url = 'http://106.ihuyi.com/webservice/sms.php?method=Submit'
            # 定义请求的数据
            values = {
                'account': 'C28994660',
                'password': 'ea3e12c806c1cff7fb3a33098663e164',
                'mobile': '%s' % data['phone'],
                'content': '尊敬的%s，您好！本次打卡%s，时间为%s。' % (
                data['username'], data['result'], data['time'][11:]),
                'format': 'json',
            }
            self.out_logger(values)
            # 将数据进行编码
            data = urllib.parse.urlencode(values).encode(encoding='UTF8')
            # 发起请求
            req = urllib.request.Request(url, data)
            response = urllib.request.urlopen(req)
            res = response.read()
            # 打印结果
            self.out_logger(res.decode("utf8"))
        except Exception:
            raise

    def out_logger(self, text):
        if self.logging and self.time:
            self.logging.info(f'{text}->{self.time.strftime("%Y-%m-%d %H:%M:%S", self.time.localtime())}')
        else:
            import time
            print(f'{text}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')


if __name__ == "__main__":
    data = {"data": {'result': 'Test', 'time': 'Test', 'addr': 'Test', 'receive_email': '752484360@qq.com', 'title': 'Test'}}
    Notify().send_by_email(**data)
    # Notify().send_by_phone(**{"data": {'result': 'Test', 'time': 'Test', 'addr': 'Test', 'phone': 'Test', 'username': 'Test'}})
