from epics import PV
import time

def task1():
    time.sleep(3)
    print('task1 test')
    return 'OK'
    
def task2():
   time.sleep(3)
   print('task2 test')
   return 'OK'