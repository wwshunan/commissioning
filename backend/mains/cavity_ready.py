import time
import re
import hmac
import hashlib
import base64
import requests, json  # 导入依赖库
import urllib
import warnings
import operator
from . import celery
from epics import PV
from datetime import datetime
from .factory import redis_client

warnings.filterwarnings("error")

#sound_device_ip = 'http://192.168.6.100:5000'

readies = ['SCRF:CAV5:TUNER:DRIVE', 'SCRF:CAV9:TUNER:DRIVE', 'SCRF:CAV14:TUNER:DRIVE', 'SCRF:CAV23:TUNER:DRIVE', 'SCRF:CAV7:ITL:RF_READY']

def data(color, timestamp, msg):
    return {
        "msgtype": "markdown",
        "markdown": {
            "content": '{} <font color="{}"> {}</font>'.format(timestamp, color, msg),
        },
        "isAtAll": True
    }


@celery.task
def send_alarm_cavity(robot_id):
    headers = {'Content-Type': 'application/json'}  # 定义数据类型
    webhook = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=efb37a61-e1c0-4c79-b929-9d39ac028834'
    # 定义要发送的数据
    # "at": {"atMobiles": "['"+ mobile + "']"

    ready_pvies = [PV(ready) for ready in readies]
    
    while True:
        stop = redis_client.get(robot_id)
        if stop == b'true':
            break
        timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        for i in range(len(ready_pvies)): 
            try:
                cav_no = re.search(r'\d+', readies[i]).group()
                ready_val = ready_pvies[i].get() 
            except UserWarning:
                res = requests.post(webhook,
                                    data=json.dumps(data('comment', timestamp, '腔体{} PV量获取失败'.format(cav_no))),
                                    headers=headers)
                print(res.json())
                time.sleep(60)
                continue
		    
            if ready_val is None:
                if ready_pvies[i] == 'SCRF:CAV7:ITL:RF_READY':
                    res = requests.post(webhook,
                                       data=json.dumps(data('warning', timestamp,  "小旺温馨提示：CM2快保护网络故障，请射频保障人员尽快处理……".format(cav_no))),
                                       headers=headers)
                else:
                    res = requests.post(webhook,
                                       data=json.dumps(data('warning', timestamp,  "腔体{} PV失去连接".format(cav_no))),
                                       headers=headers)
                time.sleep(60)

            time.sleep(1)
