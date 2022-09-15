from epics import caget, caput
import numpy as np
import time, random


setlist = ['HEBT_PS:T0_CH-01:CurSet', 'HEBT_PS:T0_CV-01:CurSet', 'HEBT_PS:T2_CH-01:CurSet', 'HEBT_PS:T2_CV-01:CurSet', 'HEBT_PS:T2_CH-02:CurSet', 'HEBT_PS:T2_CV-02:CurSet', 'HEBT_PS:T2_CH-03:CurSet', 'HEBT_PS:T2_CV-03:CurSet']
monlist = ['HEBT_PS:T0_CH-01:CurMon', 'HEBT_PS:T0_CV-01:CurMon', 'HEBT_PS:T2_CH-01:CurMon', 'HEBT_PS:T2_CV-01:CurMon', 'HEBT_PS:T2_CH-02:CurMon', 'HEBT_PS:T2_CV-02:CurMon', 'HEBT_PS:T2_CH-03:CurMon', 'HEBT_PS:T2_CV-03:CurMon']


T2HR = 'SS_BD:CHAN1_AVG_SUB_OST_VAL'
SSFC = 'SS_BD:CHAN2_AVG_SUB_OST_VAL'
T2FC = 'SS_BD:CHAN0_AVG_SUB_OST_VAL'
halo1 = 'HEBT_BD:CHAN2_AVG_SUB_OST_VAL'
halo2 = 'HEBT_BD:CHAN3_AVG_SUB_OST_VAL'
halo3 = 'HEBT_BD:CHAN7_AVG_SUB_OST_VAL'
halo4 = 'HEBT_BD:CHAN5_AVG_SUB_OST_VAL'
halo5 = 'HEBT_BD:CHAN6_AVG_SUB_OST_VAL'


g1 = caget(setlist[0])
g2 = caget(setlist[1])

lb = [-180, -180, -180, -180, -180, -180, -180, -180]
ub = [ 180,  180,  180,  180,  180,  180,  180,  180]
freq = float(input("Freq(Hz) = "))
step = 1 / freq
fc1 = 5.
w = 5. / fc1
record = []
record_mode = False
record_value = []

def gety1(repeat, p=False, mode=1): # for T2FC max
    global w, step, record
    ilist2 = np.zeros(repeat)
    for i in range(repeat):
        ilist2[i] = caget(T2FC)
        time.sleep(step)
    current2 = np.median(ilist2)
    if mode==2:
        print(ilist2)
    if p:
        print(round(current2, 2))
    return current2

def gety2(repeat, p=False, mode=1): # for SSFC max 
    global w, step, record
    ilist2 = np.zeros(repeat)
    for i in range(repeat):
        ilist2[i] = caget(SSFC)
        time.sleep(step)
    current2 = np.median(ilist2)
    if mode==2:
        print(ilist2)
    if p:
        print(round(current2, 2))
    return current2
    
def gety(repeat, p=False, mode=1): # for halo min 
    global w, step, record
    ilist2 = np.zeros(repeat)
    ilist3 = np.zeros(repeat)
    ilist4 = np.zeros(repeat)   
    ilist5 = np.zeros(repeat)   
    ilist6 = np.zeros(repeat)   
    ilist7 = np.zeros(repeat)      
    ilist8 = np.zeros(repeat)          
    for i in range(repeat):
        ilist2[i] = caget(T2HR)
        ilist3[i] = caget(halo1)
        ilist4[i] = caget(halo2)
        ilist5[i] = caget(halo3)
        ilist6[i] = caget(halo4)  
        ilist7[i] = caget(halo5) 
        ilist8[i] = caget(SSFC)  
        time.sleep(step)
    current2 = np.median(ilist8) / 2.0 - np.median(ilist2) - np.median(ilist3) - np.median(ilist4) - np.median(ilist5) - np.median(ilist6) - np.median(ilist7)
    #current2 = - np.median(ilist2) - np.median(ilist3) - np.median(ilist4) - np.median(ilist5) - np.median(ilist6) - np.median(ilist7) 
    if mode==2:
        print(ilist2)
    if p:
        print(round(current2, 2))
    return current2

def gety4(repeat, p=False, mode=1):
    global w, step, record
    ilist1 = np.zeros(repeat)
    ilist2 = np.zeros(repeat)
    for i in range(repeat):
        ilist1[i] = caget(acct1)
        ilist2[i] = caget(T2FC)
        time.sleep(step)
    current1 = np.median(ilist1)
    current2 = np.median(ilist2)
    record = [current2, current2 / current1]
    if p:
        print(round(current2, 2), str(round(current2 / current1 * 100, 2)) + '%')
    if mode == 2:
        return current2 / current1 / w * 50
    return current2

def run(repeat, mode=1):
    global xbest, ybest, record_mode, record_value
    x = list(map(caget, setlist))
    for i in range(100):
        print(i, end=' ')
        y = gety(repeat, p=True, mode=mode)
        print(x)
        if y > ybest:
            ybest = y
            xbest = x
        if record_mode:
            record_value.append(record + x)
        idx = random.randint(0, len(setlist) - 1)
        dx = 1.0 # steers
        caput(setlist[idx], x[idx] + dx)
        time.sleep(2)
        print('y2 =', end=' ')
        y2 = gety(repeat, p=True, mode=mode)
        while caget(SSFC)<35:
            time.sleep(5)
            y2 = gety(repeat, p=True, mode=mode)
        x[idx] = np.clip(round(x[idx] + dx * w * (y2 - y), 2), lb[idx], ub[idx])
        caput(setlist[idx], x[idx])
        time.sleep(2)

    for i in range(len(xbest)):
        caput(setlist[i], xbest[i])

#x0 = [22.11, 45.64, 100.93, 36.09, 0.93, 2.08, 7.01, -50.91] # SSFC-halo max
#for i in range(len(x0)):
#    caput(setlist[i], x0[i])

xbest = []
ybest = 0
run(100, mode=1)
#ybest = 0
#run(50, mode=2)

if record_mode:
    with open('sgd.dat', 'a+') as fid:
        for y in record_value:
            output = y
            strWrite = str(output)[1:-1] + '\n'
            fid.write(strWrite)
