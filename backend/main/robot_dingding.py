import time
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

trig = 'EVG1.TRIGSRC'
trig_He = ['HWRL_CRYO:CM_01:He_02:PRES', 'HWRL_CRYO:CM_02:He_02:PRES',
           'HWRL_CRYO:CM_03:He_02:PRES', 'TAPERL_CRYO:CM_04:He_02:PRES']
HE_ALARM = 110000
mps = ['EVE1.FPS1I', 'MPS_Core:Timing_EVE1:Lock01']

trip_reasons = {
    'MPS_Core:RF_LLRF11:InST': ('低电平1保护', operator.eq, 0),
    'MPS_Core:RF_LLRF12:InST': ('低电平2保护', operator.eq, 0),
    'MPS_Core:RF_LLRF21:InST': ('低电平3保护', operator.eq, 0),
    'RFQ:LLRF:NEW:Arc_Status': ('RFQ打火保护', operator.eq, 0),
    'RFQ:LLRF:NEW:Arc_Status2': ('RFQ打火保护', operator.eq, 0),
    'LIPS_PS:HV_01:VMon': ('离子源打火保护', operator.lt, 3500),
    'MPS_Core:BD_BLM01:InST': ('Beam Loss Monitor1保护', operator.eq, 0),
    'MPS_Core:BD_BLM02:InST': ('Beam Loss Monitor2保护', operator.eq, 0),
    'MPS:MEBT:TEMP:STATUS': ('MEBT温度保护', operator.eq, 0),
    'MPS:HEBT:TEMP:STATUS': ('HEBT温度保护', operator.eq, 0),
    'MPS_Core:PS_MEBT:InST': ('MEBT电源保护', operator.eq, 0),
    'MPS_Core:PS_CM12:InST': ('CM12电源保护', operator.eq, 0),
    'MPS_Core:PS_CM3_HEBT:InST': ('CM3电源保护', operator.eq, 0),
    'MPS_Core:PS_CM4_DUMP:InST': ('HEBT温度保护', operator.eq, 0),
    'MPS_Core:VAC_RFQ:InST': ('RFQ真空保护', operator.eq, 0),
    'MPS_Core:VAC_HEBT01:InST': ('HEBT01真空保护', operator.eq, 0),
    'MPS_Core:VAC_HEBT02:InST': ('HEBT02真空保护', operator.eq, 0),
    'MPS_Core:VAC_CM01:InST': ('CM1真空保护', operator.eq, 0),
    'MPS_Core:VAC_CM02:InST': ('CM2真空保护', operator.eq, 0),
    'MPS_Core:VAC_CM03:InST': ('CM3真空保护', operator.eq, 0),
    'MPS_Core:VAC_CM04:InST': ('CM4真空保护', operator.eq, 0),
}


def data(color, timestamp, title, msg):
    return {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": '{} <font color=red> {}</font>'.format(timestamp, msg),
        },
        "isAtAll": True
    }


@celery.task
def send_alarm(robot_id):
    headers = {'Content-Type': 'application/json'}  # 定义数据类型
    webhook = 'https://oapi.dingtalk.com/robot/send?access_token=' \
              'ce2549a227866d82364e216953bf44a12fda845040928daaa1d7f068b1e5a008'
    # 定义要发送的数据
    # "at": {"atMobiles": "['"+ mobile + "']"
    alarm_count = 0
    alarm_he_count = 0
    trip = False
    alarm = False
    while True:
        stop = redis_client.get(robot_id)
        if stop == b'true':
            break
        timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        try:
            trip_reason_vals = {}
            for r in trip_reasons:
                trip_reason_vals[r] = PV(r).get(timeout=3)
        except UserWarning:
            requests.post(webhook,
                          data=json.dumps(data('comment', timestamp, 'pv量', 'MPS pv量获取失败')),
                          headers=headers)
            #requests.post(webhook, data=json.dumps(data('ORANGE', timestamp, 'MPS pv量获取失败')),
            #              headers=headers)
            time.sleep(10)
            continue

        for r in trip_reasons:
            if trip_reasons[r][1](trip_reason_vals[r], trip_reasons[r][2]) and not trip:
                res = requests.post(webhook,
                                    data=json.dumps(data('red', timestamp,  'Trip原因', trip_reasons[r][0])),
                                    headers=headers)
                print(res.json())
                break

        try:
            trig_val = PV(trig).get(timeout=3)
            mps_vals = [PV(x).get(timeout=3) for x in mps]
        except UserWarning:
            res = requests.post(webhook,
                                data=json.dumps(data('green', timestamp, 'PV量获取', 'Trip pv量获取失败')),
                                headers=headers)
            print(res.json())
            time.sleep(10)
            continue

        if trig_val == 1 or any([x == 0 for x in mps_vals]):
            trip = True
            if alarm_count % 120 == 0:
                res = requests.post(webhook,
                                    data=json.dumps(data('blue', timestamp, 'Trip', '束流Trip')),
                                    headers=headers)
                print(res.json())
            alarm_count += 1
        elif trip:
            res = requests.post(webhook,
                                data=json.dumps(data('info', timestamp, 'Trip', '束流恢复')),
                                headers=headers)  # 发送post请求
            print(res.json())
            trip = False
            alarm_count = 0

        try:
            he_vals = [PV(x).get(timeout=3) for x in trig_He]
        except UserWarning:
            res = requests.post(webhook,
                                data=json.dumps(data('comment', timestamp, 'pv量获取', '氦压pv量获取失败')),
                                headers=headers)
            print(res.json())
            time.sleep(20)
            continue

        if any([x >= HE_ALARM for x in he_vals]):
            alarm = True
            if alarm_he_count % 160 == 0:
                res = requests.post(webhook,
                                    data=json.dumps(data('warning', timestamp, '氦压', '氦压报警')),
                                    headers=headers)
                print(res.json())
            alarm_he_count += 1
        elif alarm:
            res = requests.post(webhook,
                                data=json.dumps(data('info', timestamp, '氦压', '氦压恢复')),
                                headers=headers)
            print(res.json())
            alarm = False
            alarm_he_count = 0

        alarm_he_count %= 100000

        time.sleep(0.5)
