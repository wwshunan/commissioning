from fastapi import APIRouter, Depends, HTTPException
from epics import PV
#from rq import Queue, Connection
from ..dependencies import JWTBearer
from ..services.pv_handler import PhaseScanPVController
from ..services.worker import q
from ..schemas import Orbit, OneCorrector, SavedFile, SavedBpmVar, Correctors
from pathlib import Path
import pandas as pd
import numpy as np
import json
import asyncio
import aioredis
import fastapi_plugins

router = APIRouter()
basedir = Path(__file__).resolve().parent
pv_controller = PhaseScanPVController()


#with Connection(redis.from_url('redis://127.0.0.1:6379')):
#    q = Queue()

@router.get('/commissioning/magnet-validation/get-config',
            dependencies=[Depends(JWTBearer())])
async def get_config():
    fname = basedir.joinpath('resources', 'config.json')
    with open(fname) as f:
        data = json.load(f)
    return {
        'code': 20000,
        'data': data
    }


@router.post('/commissioning/magnet-validation/get-orbit',
             dependencies=[Depends(JWTBearer())])
def get_orbit(data: Orbit):
    bpm_data = data.section_data['children'][1]['children']

    orbit = []
    for item in bpm_data:
        orbit_item = {}
        x = PV(item['x_pv']).get()
        y = PV(item['y_pv']).get()
        orbit_item['label'] = item['id']
        orbit_item['x'] = x
        orbit_item['y'] = y
        orbit.append(orbit_item)

    return {
        'code': 20000,
        'orbit': orbit
    }

async def get_orbit_var(bpms, loops):
    var = 0
    xs, ys = [], []
    for _ in range(loops):
        for item in bpms:
            x = PV(item['x_pv']).get()
            y = PV(item['y_pv']).get()
            xs.append(x)
            ys.append(y)
        await asyncio.sleep(1)
    xs = np.array(xs).reshape(loops, -1)
    ys = np.array(ys).reshape(loops, -1)
    x = np.average(xs, axis=0)
    y = np.average(ys, axis=0)
    var = np.linalg.norm(np.concatenate((x, y))) 
    return var

@router.post('/commissioning/magnet-validation/correct',
             dependencies=[Depends(JWTBearer())])
async def correct(data: Correctors):
    section_name = data.section_data['id']
    corrs = data.section_data['children'][0]['children'][:2]
    bpms = data.section_data['children'][1]['children']

    step = 0.5 if section_name == 'MEBT' else 1

    for corr in corrs:
        set_pv = PV(corr['set_pv'])
        get_pv = PV(corr['get_pv'])

        pre_bpm_var = await get_orbit_var(bpms, 3)
        count = 3
        min_var = 1000
        best_corr = set_pv.get()
        current_corr = best_corr
        while True:
            current_corr += step
            set_pv.put(round(current_corr, 1))

            while abs(get_pv.get() - current_corr) > 0.2:
                await asyncio.sleep(1)

            bpm_var = await get_orbit_var(bpms, 3)

            if bpm_var > pre_bpm_var:
                count -= 1
                step = -step

            if bpm_var < min_var:
                min_var = bpm_var
                best_corr = current_corr

            if count == 0:
                set_pv.put(round(best_corr, 1))
                break

            pre_bpm_var = bpm_var
            
    return {
        'code': 20000,
        'msg': "完成轨道校正"
    }

@router.post('/commissioning/magnet-validation/set-strength',
             dependencies=[Depends(JWTBearer())])
async def set_strength(data: OneCorrector):
    step = data.step
    set_pv = PV(data.set_pv)
    get_pv = PV(data.get_pv)
    current = set_pv.get() 
    if abs(current + step) > data.limit:
        step *= -1
    target_current = current + step
    set_pv.put(round(target_current, 1))
    
    while target_current - get_pv.get() > 0.2:
        await asyncio.sleep(0.5)

    related_filename = basedir.joinpath('resources', 'causality.xlsx')
    cor_bpm_relation = pd.read_excel(related_filename)
    selected_bpms = cor_bpm_relation[cor_bpm_relation[data.name] == 1]['Bpms']
    start_bpm = ''
    print(selected_bpms.empty)
    if not selected_bpms.empty:
        start_bpm = selected_bpms.iloc[0]
    return {
        'code': 20000,
        'step': step,
        'start_bpm': start_bpm
    }


@router.post('/commissioning/magnet-validation/recover-corr',
             dependencies=[Depends(JWTBearer())])
async def recover_corr(data: OneCorrector):
    step = data.step
    set_pv = PV(data.set_pv)
    current = set_pv.get()
    set_pv.put(round(current-step, 1))

    return {
        'code': 20000
    }

@router.post('/commissioning/magnet-validation/save-data',
             dependencies=[Depends(JWTBearer())])
async def save_data(data: SavedBpmVar,
                    cache: aioredis.Redis = Depends(fastapi_plugins.depends_redis)):
    bpm_names, var_xs, var_ys = data.bpm_names, data.bpm_var_xs, data.bpm_var_ys

    filename = await cache.get('saved_file')
    if filename:
        out_file = basedir.joinpath('files', filename.decode('utf-8'))
        file_existed = out_file.is_file()
        with open(out_file, 'a') as f:
            if not file_existed:
                f.write("cor-name cor-variation bpm-name bpm-x bpm-y\n")
            for bpm_name, var_x, var_y in zip(bpm_names, var_xs, var_ys):
                f.write(f"{data.corr} {data.step} {bpm_name} {var_x:.1f} {var_y:.1f}\n")
    return {
        'code': 20000
    }

@router.post('/commissioning/magnet-validation/create-saved-file',
             dependencies=[Depends(JWTBearer())])
async def create_saved_file(data: SavedFile,
                            cache: aioredis.Redis = Depends(fastapi_plugins.depends_redis)):
    filename = data.filename
    if not Path(filename).suffix:
        filename += '.txt'
    saved_file = basedir.joinpath('files', filename)
    if not saved_file.is_file():
        await cache.set('saved_file', saved_file.name)
        return {
            'code': 20000,
            'msg': "文件成功创建"
        }
    else:
        return {
            'code': 409,
            'message': "文件已存在，请选择另一文件名!"
        }
        
