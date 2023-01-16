from epics import PV
from ..exceptions import raise_exception
import time
import os

base_dir = os.path.dirname(os.path.abspath(__file__))


def open_fc1():
    time.sleep(5)
    if PV('Bpm:1-X11').get() > 2:
        raise_exception('BPM轨道超阈值')
    return 'FC1已打开'

def open_fc2():
    time.sleep(5)
    return 'FC2已打开'

def close_fc2():
    time.sleep(5)
    return 'FC2处于关闭状态'

def lebt_status_check():
    time.sleep(5)
    return 'LEBT正常'

def mebt_status_check():
    time.sleep(5)
    return 'MEBT正常'

def sc_status_check():
    time.sleep(5)
    return 'SC正常'

def hebt_status_check():
    time.sleep(5)
    return 'HEBT正常'

def valve_status_check():
    time.sleep(10)
    return '所有阀门已打开'

def intercept_status_check():
    time.sleep(10)
    return 'MEBT和高能段束诊元件已打开'

def rfq_transit_check():
    time.sleep(10)
    return 'RFQ传输效率高于96%'
