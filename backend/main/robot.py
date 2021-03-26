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

HE_ALARM = 120000
#sound_device_ip = 'http://192.168.6.100:5000'

trig = 'EVG1.TRIGSRC'
trig_He = ['HWRL_CRYO:CM_01:He_02:PRES', 'HWRL_CRYO:CM_02:He_02:PRES',
           'HWRL_CRYO:CM_03:He_02:PRES', 'TAPERL_CRYO:CM_04:He_02:PRES']
mps = ['EVE1.FPS1I', 'MPS_Core:Timing_EVE1:Lock01']

trip_reasons = {
    'MPS_Core:RF_LLRF11:InST': ('低电平1保护', operator.eq, 0),
    'MPS_Core:RF_LLRF12:InST': ('低电平2保护', operator.eq, 0),
    'MPS_Core:RF_LLRF21:InST': ('低电平3保护', operator.eq, 0),
    'RFQ:LLRF:NEW:Arc_Status2': ('RFQ打火保护', operator.eq, 0),
    'LIPS_PS:HV_01:VMon': ('离子源打火保护', operator.lt, 19),
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


def data(color, timestamp, msg):
    return {
        "msgtype": "markdown",
        "markdown": {
            "content": '{} <font color="{}"> {}</font>'.format(timestamp, color, msg),
        },
        "isAtAll": True
    }


@celery.task
def send_alarm(robot_id):
    headers = {'Content-Type': 'application/json'}  # 定义数据类型
    webhook = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=efb37a61-e1c0-4c79-b929-9d39ac028834'
    # 定义要发送的数据
    # "at": {"atMobiles": "['"+ mobile + "']"
    alarm_count = 0
    alarm_he_count = 0
    trip = False
    alarm = False
    trip_reason_set = False
    trip_reason_obj = {x: PV(x) for x in trip_reasons}
    trig_obj = PV(trig)
    mps_obj = [PV(x) for x in mps]
    trig_He_obj = [PV(x) for x in trig_He]
    valid_to_compare = True
    
    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    requests.post(webhook,
		  data=json.dumps(data('info', timestamp, '小旺全天候为您守护')),
		  headers=headers)
    while True:
        stop = redis_client.get(robot_id)
        timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        if stop == b'true':
            requests.post(webhook,
                          data=json.dumps(data('comment', timestamp, '机器人停止')),
                          headers=headers)
            break

        try:
            trip_reason_vals = {}
            for x in trip_reason_obj:
                trip_reason_vals[x] = int(trip_reason_obj[x].get(timeout=3))
        except TypeError:
            requests.post(webhook,
                          data=json.dumps(data('comment', timestamp, 'MPS pv量获取失败')),
                          headers=headers)
            #requests.post(webhook, data=json.dumps(data('ORANGE', timestamp, 'MPS pv量获取失败')),
            #              headers=headers)
            time.sleep(10)
            continue

        for r in trip_reasons:
            #print('reason', r, trip_reason_vals[r])
            if trip_reason_vals[r] is None:
                res = requests.post(webhook,
                                    data=json.dumps(data('warning', timestamp,  "{} {}".format(r, "失去连接"))),
                                    headers=headers)
                break
            if all([trip_reasons[r][1](trip_reason_vals[r], trip_reasons[r][2]), not trip_reason_set]):
                res = requests.post(webhook,
                                    data=json.dumps(data('warning', timestamp,  trip_reasons[r][0])),
                                    headers=headers)
                print(res.json())
#                requests.post(sound_device_ip,
#                              data=json.dumps({'text': trip_reasons[r][0]}),
#                              headers=headers)
                trip_reason_set = True
                break

        try:
            trig_val = trig_obj.get(timeout=3)
            mps_vals = [o.get(timeout=3) for o in mps_obj]
        except UserWarning:
            res = requests.post(webhook,
                                data=json.dumps(data('comment', timestamp, 'Trip pv量获取失败')),
                                headers=headers)
            print(res.json())
            time.sleep(10)
            continue
            
        for x in [*mps_vals, trig_val]:
            if x is None:
                res = requests.post(webhook,
                                    data=json.dumps(data('warning', timestamp,  "mps PV失去连接")),
                                    headers=headers)
                valid_to_compare = False
                break
                
        if valid_to_compare and (trig_val == 1 or any([x == 0 for x in mps_vals])):
            trip = True
            if alarm_count % 180 == 0:
                res = requests.post(webhook,
                                    data=json.dumps(data('warning', timestamp, '束流Trip')),
                                    headers=headers)
#                requests.post(sound_device_ip,
#                              data=json.dumps({'text': '束流掉了'}),
#                              headers=headers)
                print(res.json(), 'beam trip')
            alarm_count += 1
        elif trip:
            res = requests.post(webhook,
                                data=json.dumps(data('info', timestamp, '束流恢复')),
                                headers=headers)  # 发送post请求
            print(res.json(), 'beam recover')
            trip = False
            trip_reason_set = False
            alarm_count = 0

        try:
            he_vals = [x.get(timeout=3) for x in trig_He_obj]
        except UserWarning:
            res = requests.post(webhook,
                                data=json.dumps(data('comment', timestamp, '氦压pv量获取失败')),
                                headers=headers)
            print(res.json())
            time.sleep(20)
            continue
            
        for x in he_vals:
            if x is None:
                res = requests.post(webhook,
                                    data=json.dumps(data('warning', timestamp,  "He PV失去连接")),
                                    headers=headers)
                valid_to_compare = False
                break
                
        if valid_to_compare and any([x >= HE_ALARM for x in he_vals]):
            alarm = True
            if alarm_he_count % 180 == 0:
                res = requests.post(webhook,
                                    data=json.dumps(data('warning', timestamp, '氦压报警')),
                                    headers=headers)
#                requests.post(sound_device_ip,
#                              data=json.dumps({'text': '氦压报警'}),
#                              headers=headers)
                print(res.json(), 'he recover')
            alarm_he_count += 1
        elif alarm:
            res = requests.post(webhook,
                                data=json.dumps(data('info', timestamp, '氦压恢复')),
                                headers=headers)
            print(res.json())
            alarm = False
            alarm_he_count = 0

        alarm_he_count %= 100000

        time.sleep(0.4)
