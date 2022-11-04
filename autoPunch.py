"""
@Coding:utf-8
@Author:XiaoL
@Time:2022/8/11 14:33
@File:auto
@Software:PyCharm
"""

import logging
import time
import json
import asyncio
import random
import execjs
import websockets as ws
import datetime
from chinese_calendar import is_holiday
from auto_punch_notify import Notify
from auto_punch_mysql import DBHandle
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

# 定义用户数据
token = []
latitude, longitude = '', ''
wss_url = ''
punch_config = []
notify_config = []
# 定义请求数据
temp_login = ''
command_connect = ''
command_ping = ''
command_getGeoAddress = ''
command_punch = ''
command_update_punch = ''
command_attendance_init = ''
command_attendances = ''
command_todoTaskCount = ''

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S', filename='auto_punch_log.txt', filemode='a')
# 创建logger对象
logger = logging.getLogger('logger')
# 创建控制台
console = logging.StreamHandler()
# 设置控制台日志等级
console.setLevel(logging.INFO)
# 加载控制台实例到logger对象中
logger.addHandler(console)
# 配置调度器
scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


def shuffle_str(s):
    # 将字符串转换成列表
    str_list = list(s)
    # 调用random模块的shuffle函数打乱列表
    random.shuffle(str_list)
    # 将列表转字符串
    return ''.join(str_list)


def js_from_file(file_name):
    """
    读取js文件
    :return:
    """
    with open(file_name, 'r', encoding='UTF-8') as file:
        result = file.read()

    return result


# 配置初始化数据
async def init_data():
    # 声明全局变量
    global latitude, longitude, wss_url, temp_login, command_connect, command_ping, command_getGeoAddress, command_punch, command_update_punch, command_punch, command_attendance_init, command_attendances, command_todoTaskCount
    latitude, longitude = '24.342749285961194', '109.42300104879952'
    wss_url = "wss://icloudportal.com/sockjs/853/2ih63_c4/websocket"
    # 配置请求数据
    temp_login = r'["{\"msg\":\"method\",\"method\":\"login\",\"params\":[{\"resume\":\"%s\"}],\"id\":\"1\"}"]'
    command_connect = r'["{\"msg\":\"connect\",\"version\":\"1\",\"support\":[\"1\",\"pre2\",\"pre1\"]}"]'
    command_ping = r'["{\"msg\":\"pong\"}"]'
    command_getGeoAddress = r'["{\"msg\":\"method\",\"method\":\"getGeoAddress\",\"params\":[{\"latitude\":%s,\"longitude\":%s}],\"id\":\"46\"}"]' % (latitude, longitude)
    command_punch = r'["{\"msg\":\"method\",\"method\":\"punch\",\"params\":[\"$params\",{\"coords\":{\"latitude\":%s,\"longitude\":%s},\"baiduCoords\":{\"longitude\":%s,\"latitude\":%s},\"address\":\"$address\"}],\"id\":\"47\"}"]' % (latitude, longitude, longitude, latitude)
    # 更新打卡
    command_update_punch = r'["{\"msg\":\"method\",\"method\":\"updatePunch\",\"params\":[{\"coords\":{\"latitude\":24.342749539653884,\"longitude\":109.4230016070517},\"baiduCoords\":{\"longitude\":24.346311562678885,\"latitude\":109.43403642150422},\"address\":\"广西壮族自治区柳州市城中区海关路10-22号\"},\"WaS7BGBFH9pTDHsqp\",1,\"end\"],\"id\":\"22\"}"]'
    today_start = (time.localtime().tm_hour * 60 * 60 * 1000) + (time.localtime().tm_min * 60 * 1000) + (time.localtime().tm_sec * 1000)
    today_end = ((23 - time.localtime().tm_hour) * 60 * 60 * 1000) + ((59 - time.localtime().tm_min) * 60 * 1000) + ((59 - time.localtime().tm_sec) * 1000)
    ts = str(time.time() * 1000 - today_start)[0:9] + "0000"
    te = str(time.time() * 1000 + today_end)[0:9] + "9999"
    command_attendance_init = r'["{\"msg\":\"method\",\"method\":\"attendanceInit\",\"params\":[{\"$date\":%s},{\"$date\":%s},-480,{\"$date\":%s}],\"id\":\"4\"}"]' % (ts, te, int(time.time() * 1000))
    command_attendances = r'["{\"msg\":\"sub\",\"id\":\"$id\",\"name\":\"attendances\",\"params\":[{\"$date\":%s},{\"$date\":%s}]}"]' % (ts, te)
    command_todoTaskCount = r'["{\"msg\":\"method\",\"method\":\"todoTaskCount\",\"params\":[{\"organization\":\"$organization\"}],\"id\":\"5\"}"]'


# 关闭与服务器连接
async def close_connect(websocket):
    await websocket.close(reason="exit")


# 执行相关请求
async def handle_msg(websocket, command_login, punch_cfg, notify_cfg):
    recv_data, attendances_id, organization, address, punch_result, attendances_result, phone = None, None, None, None, False, False, None
    while True:
        try:
            recv_data = await websocket.recv()
            logger.info(f'服务器响应消息：{recv_data}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
            data = json.loads(recv_data[1:len(recv_data)])
            if "server_id" in json.loads(data[0]):
                if json.loads(data[0])["server_id"] == "0":
                    logger.info(f'服务器响应：server_id->{json.loads(data[0])["server_id"]}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
                    logger.info(f'发送连接请求：{command_connect}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
                    await websocket.send(command_connect)
            if "msg" in json.loads(data[0]):
                logger.info(f'服务器消息：msg->{json.loads(data[0])["msg"]}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
                if json.loads(data[0])["msg"] == "ping":
                    logger.info(f'发送响应：{command_ping}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
                    await websocket.send(command_ping)
                if json.loads(data[0])["msg"] == "connected":
                    logger.info(f'发送登录请求：{command_login}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
                    await websocket.send(command_login)
                if json.loads(data[0])["msg"] == "added":
                    if "collection" in json.loads(data[0]):
                        if json.loads(data[0])["collection"] == "employees":
                            phone = json.loads(data[0])["fields"]["phones"][0]["number"]
                            logger.info(f'用户号码：{phone}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
                            # 测试短信消息
                            # Notify().send_by_phone(**{"data": {'result': '成功', 'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),'addr': address, 'phone': phone, 'username': '用户'}})
                            # 更新签到请求
                            # temp = command_update_punch.replace("$params", attendances_id, 1).replace("$address", address, 1)
                            # 直接签到请求
                            temp = command_punch.replace("$params", attendances_id, 1).replace("$address", address, 1)
                            logger.info(f'发送签到请求：{temp}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
                            await websocket.send(temp)
                            punch_result = True
                        if json.loads(data[0])["collection"] == "users":
                            logger.info(f'用户信息：{json.loads(data[0])["fields"]["profile"]["name"]}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
                            organization = json.loads(data[0])["fields"]["profile"]["organization"]
                        if json.loads(data[0])["collection"] == "attendances" and attendances_result is True:
                            attendances_id = json.loads(data[0])["id"]
                            logger.info(f'考勤信息ID：{attendances_id}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
                            logger.info(f'发送获取物理位置请求：{command_getGeoAddress}->{time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())}')
                            await websocket.send(command_getGeoAddress)
                if json.loads(data[0])["msg"] == "changed":
                    if "collection" in json.loads(data[0]):
                        if json.loads(data[0])["collection"] == "attendances" and punch_result is True:
                            if "records" in json.loads(data[0])["fields"]:
                                temp = json.loads(data[0])["fields"]["records"]
                                for item in temp:
                                    if "start" in item:
                                        if "time" in item["start"]:
                                            start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item["start"]["time"]["$date"] / 1000))
                                            logger.info(f'签到开始：{item["start"]["location"]["office"]}-{start_time}-{item["start"]["result"]}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
                                    if "end" in item:
                                        if "time" in item["end"]:
                                            end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item["end"]["time"]["$date"] / 1000))
                                            logger.info(f'签到结束：{item["end"]["location"]["office"]}-{end_time}-{item["end"]["result"]}->{time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())}')
                            try:
                                data_config = {"data": {'result': '成功', 'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'addr': '不显示', 'receive_email': json.loads(notify_cfg)["email"], 'title': '云签到通知'}};
                                Notify().send_by_email(**data_config)
                                # Notify().send_by_phone(**{"data": {'result': '成功', 'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),'addr': address, 'phone': phone, 'username': '用户'}})
                            except Exception as e:
                                logger.info(f'发送提示出错：{e}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
                            finally:
                                await close_connect(websocket)
                                break
                if json.loads(data[0])["msg"] == "result":
                    if "error" in json.loads(data[0]):
                        logger.info(f'发生错误：{json.loads(data[0])}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
                        await close_connect(websocket)
                        break
                    if "result" in json.loads(data[0]):
                        if "tokenExpires" in json.loads(data[0])["result"]:
                            logger.info(f'Token有效期：{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(json.loads(data[0])["result"]["tokenExpires"]["$date"]/1000))}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')

                            # 初始化开始
                            logger.info(f'发送初始化考勤请求：{command_attendance_init}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
                            await websocket.send(command_attendance_init)
                            temp = command_todoTaskCount.replace("$organization", organization, 1)
                            logger.info(f'发送获取计划数量请求：{temp}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
                            await websocket.send(temp)
                            # 初始化结束

                            sub_id = command_attendances.replace("$id", shuffle_str('aAqYdmieuoi7D5uqb'), 1)
                            logger.info(f'发送获取考勤信息请求：{sub_id}->{time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())}')
                            await websocket.send(sub_id)
                            attendances_result = True
                        if "address" in json.loads(data[0])["result"]:
                            address = json.loads(data[0])["result"]["address"]
                            logger.info(f'物理地址：{address}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
                            # 获取用户号码
                            await websocket.send(r'["{\"msg\":\"sub\",\"id\":\"%s\",\"name\":\"current-employee\",\"params\":[]}"]' % shuffle_str('EWp7r2v4SkSTxGLHy'))
        except KeyError as e:
            logger.info(f'属性异常：{e}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
            break
        except (AttributeError, json.JSONDecodeError, TypeError) as e:
            logger.info(f'数据解析异常：{e}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
        except (ConnectionRefusedError, ConnectionError, ws.ConnectionClosedError, ws.ConnectionClosedOK) as e:
            logger.info(f'服务器连接关闭：{e}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
            break
        except KeyboardInterrupt:
            logger.info(f'程序被主动中断->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
            break


async def handle_token(websocket, command_login):
    global token
    while True:
        try:
            recv_data = await websocket.recv()
            logger.info(f'服务器响应消息：{recv_data}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
            data = json.loads(recv_data[1:len(recv_data)])
            if "server_id" in json.loads(data[0]):
                if json.loads(data[0])["server_id"] == "0":
                    logger.info(f'服务器响应：server_id->{json.loads(data[0])["server_id"]}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
                    logger.info(f'发送连接请求：{command_connect}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
                    await websocket.send(command_connect)
            if "msg" in json.loads(data[0]):
                logger.info(f'服务器消息：msg->{json.loads(data[0])["msg"]}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
                if json.loads(data[0])["msg"] == "ping":
                    logger.info(f'发送响应：{command_ping}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
                    await websocket.send(command_ping)
                if json.loads(data[0])["msg"] == "connected":
                    logger.info(f'发送获取Token请求：{command_login}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
                    await websocket.send(command_login)
                if json.loads(data[0])["msg"] == "result":
                    logger.info(f'加入Token到列表：{json.loads(data[0])["result"]["token"]}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
                    token.append(json.loads(data[0])["result"]["token"])
                    await close_connect(websocket)
                    break
                if "error" in json.loads(data[0]):
                    logger.info(f'发生错误：{json.loads(data[0])}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
                    await close_connect(websocket)
                    break
        except Exception as e:
            logger.info(f"{e}发生异常")


# 主任务控制
async def main_task():
    global punch_config, notify_config
    # 编译加载js字符串
    context = execjs.compile(js_from_file('./encrypt.js'))
    # 调用初始化登录信息
    await init_login()
    # 获取数据库
    user_data = DBHandle(logger=logger, time=time)
    for user in user_data.query_db():
        user_data.out_logger(user)
        # 如果是节假日则跳过
        date = time.localtime(time.time())
        if is_holiday(datetime.datetime(date[0], date[1], date[2])):
            user_data.out_logger(text="节假日不打卡")
            break
        if user[5] != 1:
            user_data.out_logger(text="未启用的配置")
            continue
        command_login = temp_login % (user[1], context.call('encrypt', user[2]))
        punch_config.append(user[3])
        notify_config.append(user[4])
        # 处理登录任务
        async with ws.connect(wss_url) as websocket:
            # 获取Token
            await handle_token(websocket, command_login)
    # 输出Token列表
    user_data.out_logger('Token列表：' + str(token))
    # 调用初始化签到数据
    await init_data()
    # 处理签到任务
    async_scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
    # 随机时间处理
    list_ = random___(len(token))
    for index in range(len(token)):
        async_scheduler.add_job(func=task, args=(index,), next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=list_[index]*60))
    async_scheduler.start()


def random___(length):
    list_ = set()
    while len(list_) < length:
        list_.add(random__())
    list_ = list(list_)
    random.shuffle(list_)
    logger.info(f'{list_}->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
    return list_


def random__():
    # 按分钟处理
    a, b, c = random_(10, 29), random_(11, 29), random_(12, 29)
    while True:
        if random_() < 20:
            return a
        if 20 <= random_() < 40:
            return b
        if random_() >= 40:
            return c


async def task(index):
    # print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    command_login = temp_login % token[index]
    logger.info(f'正在执行第{index + 1}个任务，连接中...->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
    async with ws.connect(wss_url) as websocket:
        await handle_msg(websocket, command_login, punch_config[index], notify_config[index])


# 初始化登录信息
async def init_login():
    # 声明全局变量
    global token, punch_config, notify_config, wss_url, temp_login, command_connect
    token = []
    punch_config = []
    notify_config = []
    wss_url = "wss://accounts.icloudportal.com/sockjs/970/gxonj64h/websocket"
    command_connect = r'["{\"msg\":\"connect\",\"version\":\"1\",\"support\":[\"1\",\"pre2\",\"pre1\"]}"]'
    temp_login = r'["{\"msg\":\"method\",\"method\":\"login\",\"params\":[{\"user\":{\"email\":\"%s\"},\"password\":{\"digest\":\"%s\",\"algorithm\":\"sha-256\"}}],\"id\":\"2\"}"]'


# WebSocket异常监听
def listener(event):
    if event.exception:
        logger.info(f"{event.job_id}出错了")
    else:
        logger.info(f"正常执行")


# 生成随机秒数
def random_(min_=0, max_=60):
    return random.randint(min_, max_)


if __name__ == "__main__":
    # asyncio.new_event_loop().run_until_complete(main_task())
    scheduler.add_job(func=main_task, trigger="cron", day_of_week="0-6", hour=8, minute=0, second=0, jitter=0)
    scheduler.add_job(func=main_task, trigger="cron", day_of_week="0-6", hour=18, minute=0, second=0, jitter=0)
    scheduler.add_listener(listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    scheduler._logger = logger
    scheduler.start()
    logger.info(f"AutoPunchRunning...")
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        logger.info(f'程序被主动中断->{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
