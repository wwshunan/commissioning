from fastapi import (APIRouter, Depends, UploadFile, File, Form,
                     WebSocket, HTTPException, Security)
from rq import Queue
from epics import PV
from sqlalchemy.orm import Session
from datetime import datetime
from ..crud import log_epk_item, get_physic_amp, get_amp_limt, create_phase_scan_log
from ..services.worker import conn
from ..dependencies import JWTBearer, get_db
from ..services.pv_handler import PhaseScanPVController
import pandas as pd
from pathlib import Path
from ..schemas import (PhaseScanInfo, CurveFitInfo, SmoothData, CavityFinished,
                       CavityModel, SynchPhaseModel, CavityAmp)
from .phase_fit import PhaseFit
from .smooth import smooth_data
import fastapi_plugins
import aioredis
import numpy as np
import time
import json
import asyncio

router = APIRouter()
basedir = Path(__file__).resolve().parent
pv_controller = PhaseScanPVController()
q = Queue(connection=conn)


@router.get('/commissioning/phasescan/config',
            dependencies=[Depends(JWTBearer())])
async def config(cache: aioredis.Redis = Depends(fastapi_plugins.depends_redis)):
    fname = basedir.joinpath('resources', 'config.txt')
    cavity_infos = pd.read_csv(fname, header=0, sep=r'\s+')
    cavity_infos = cavity_infos.set_index('cavity_name')
    serialized_lattice_data = json.dumps(cavity_infos.to_dict())
    await cache.set('cavity_infos', serialized_lattice_data)
    return {
        'code': 20000,
        'cavity_infos': cavity_infos.to_dict('index')
    }


@router.post('/commissioning/phasescan/init-pvs',
             dependencies=[Depends(JWTBearer())])
async def init_pvs(cavity_info: CavityModel,
                   cache: aioredis.Redis = Depends(fastapi_plugins.depends_redis)):
    # monitor_cols = ['phase_write_pv', 'phase_readback_pv', 'ready_pv', 'bpm1_pv', 'bpm2_pv']
    params_one_cavity = ['amp_limit_pv', 'bpm1_pv', 'bpm2_pv', 'bpm3_pv', 'current_ready', 'x', 'y']
    # phases = pd.read_csv(basedir.joinpath('resources', 'synch_phases.txt'),
    #                     header=0, sep='\s+')
    pvs = pd.read_csv(basedir.joinpath('resources', 'config.txt'),
                      header=0, sep='\s+')
    # row_idx = phases[phases['cavity_name'] == cavity_info.cavity_name].index.values[0]
    # cavities_monitor = phases.loc[:row_idx, 'cavity_name'].tolist()

    # monitor_pvs = {}
    # for col in monitor_cols:
    #    monitor_pvs[col] = []
    #    # pv_controller.pvs[col] = {}
    #    pvs_item = pvs.loc[pvs['cavity_name'].isin(cavities_monitor), col]
    #    monitor_pvs[col] = pvs_item.values.ravel()
    pvs.set_index('cavity_name', inplace=True)
    pv_controller.finished.put(json.dumps({cavity_info.cavity_name: False}))
    for label in params_one_cavity:
        pv_name = pvs.loc[cavity_info.cavity_name, label]
        if '|' in pv_name:
            pv_single, pv_double = pv_name.split('|')
            pv_controller.pvs_one_cavity[label] = (PV(pv_single), PV(pv_double))
        else:
            pv_controller.pvs_one_cavity[label] = PV(pv_name)

    for cavity_name in pvs.index:
        pv_controller.amps[cavity_name] = PV(pvs.loc[cavity_name, 'amp_write_pv'])
        pv_controller.phases[cavity_name] = PV(pvs.loc[cavity_name, 'phase_write_pv'])
        pv_controller.cavity_bypass[cavity_name] = PV(pvs.loc[cavity_name, 'cavity_bypass'])

    await cache.set('start_time', datetime.utcnow().isoformat())
    await cache.set('bpm1_name', pvs.loc[cavity_info.cavity_name, 'bpm1_name'])
    await cache.set('bpm2_name', pvs.loc[cavity_info.cavity_name, 'bpm2_name'])

    for key in ['rf_phases', 'bpm1_phases', 'bpm1_errors', 'bpm2_phases', 'bpm2_errors']:
        await cache.delete(key)
    # pv_controller.register_pvs(monitor_pvs)
    # job = q.enqueue_call(
    #    func=pv_controller.monitor, result_ttl=5000
    # )

    # monitor_pvs = pvs.loc[pvs['cavity_name'].isin(cavities_monitor), col]
    # monitor_pvs = monitor_pvs.values.ravel()
    # for pv in monitor_pvs:
    #    pv_controller.pvs[col][pv] = PV(pv)

    return dict(code=20000, message="success")


# @app.route("/commissioning/get_ready/<job_key>", methods=['GET'])
# def get_ready(job_key):
#    job = Job.fetch(job_key, connection=conn)
#    if job.is_finished:
#        return dict(code=20000, is_ready=job.result)
#    raise HTTPException(status_code=202)


# @router.post('/commissioning/phasescan/single-bpm-phase-set',
#             dependencies=[Depends(JWTBearer())])
# def double_phase_set(data: PhaseScanInfo):
#    phase_pv = pv_controller.pvs['phase_write_pv'][data.cavity_write_pv]
#    # phase_pv = PV(data.cavity_write_pv)
#    phase_pv.put(data.cavity_phase_val)
#    time.sleep(data.cavity_response_time)
#    bpm_vals = []
#    bpm_pv_name = data.bpm1_phase_pv
#    bpm_pv = pv_controller.pvs['bpm1_pv'][bpm_pv_name]
#    # bpm_pv = PV(bpm_pv_name)
#
#    for _ in range(data.bpm_read_num):
#        bpm_val = bpm_pv.get()
#        bpm_vals.append(bpm_val)
#        time.sleep(data.bpm_read_sep)
#    bpm_val = np.average(bpm_vals)
#    bpm_err = np.std(bpm_vals)
#    return {
#        'code': 20000,
#        'point1': {'x': data.cavity_phase_val,
#                   'y': bpm_val,
#                   'err': bpm_err
#                   },
#    }

@router.get('/commissioning/phasescan/read-lattice-cache',
            dependencies=[Depends(JWTBearer())])
async def read_lattice_cache(cache: aioredis.Redis = Depends(fastapi_plugins.depends_redis)):
    lattice_cache = await cache.get('stored_lattice')
    lattice = ''
    if lattice_cache:
        lattice = json.loads(lattice_cache)
    return {
        'code': 20000,
        'lattice': lattice
    }

@router.post('/commissioning/phasescan/synch-phase-set',
             dependencies=[Depends(JWTBearer())])
async def synch_phase_set(data: SynchPhaseModel,
                          db: Session = Depends(get_db),
                          cache: aioredis.Redis = Depends(fastapi_plugins.depends_redis)):

    await cache.set('stored_lattice', json.dumps(data.lattice))
    for cavity_name in data.lattice:
        amp = data.lattice[cavity_name]['amp']
        phase = data.lattice[cavity_name]['phase']
        pv_controller.set_cavity_amp(cavity_name, amp)
        pv_controller.set_cavity_phase(cavity_name, phase)

    time.sleep(2)
    general_data = {}
    general_keys = ['cavity_name', 'start_time', 'physics_amp', 'rf_amp', 'synch_phase',
                    'rf_phase', 'bpm1_name', 'bpm2_name', 'energy']
    bpm_phase_check = pv_controller.pvs_one_cavity["bpm1_pv"].get()
    for k in general_keys:
        general_data[k] = await cache.get(k)
        general_data[k] = general_data[k].decode('utf-8')
    general_data['start_time'] = datetime.fromisoformat(general_data['start_time'])
    general_data['bpm_phase_check'] = bpm_phase_check
    raw_data_keys = ['rf_phases', 'bpm1_phases', 'bpm1_errors', 'bpm2_phases', 'bpm2_errors']
    raw_data = {}
    for k in raw_data_keys:
        data = await cache.lrange(k, 0, -1)
        raw_data[k] = data
    create_phase_scan_log(db, general_data, raw_data)

    return dict(code=20000, message="腔体同步相位已设置")


@router.post('/commissioning/phasescan/calibrated-amp',
             dependencies=[Depends(JWTBearer())])
async def calibrated_amp(cavity: CavityAmp):
    amp = json.dumps({cavity.cavity_name: cavity.amp})
    pv_controller.calibrated_epk.put(amp)
    return dict(code=20000, message="腔体Epeak已发送")

@router.get('/commissioning/phasescan/read-bpm-phase',
             dependencies=[Depends(JWTBearer())])
async def read_bpm_phase(cache: aioredis.Redis = Depends(fastapi_plugins.depends_redis)):
    bpm_vals = []
    for i in range(6):
        bpm1_val = pv_controller.pvs_one_cavity['bpm1_pv'][0].get()
        bpm_vals.append(bpm1_val)
        await asyncio.sleep(1)
    bpm_name = await cache.get('bpm1_name')
    bpm_name = bpm_name.decode('utf-8')
    return {
        'code': 20000,
        'bpm_name': bpm_name,
        'bpm_phase': round(np.average(bpm_vals), 2)
    }

@router.post('/commissioning/phasescan/get-amp',
             dependencies=[Depends(JWTBearer())])
async def get_amp(cavity: CavityModel,
                  db: Session = Depends(get_db),
                  cache: aioredis.Redis = Depends(fastapi_plugins.depends_redis)):
    cavity_name = cavity.cavity_name
    cavity_infos = await cache.get('cavity_infos')
    cavity_infos = json.loads(cavity_infos)
    # config_fname = basedir.joinpath('resources', 'config.txt')
    # config_infos = pd.read_csv(config_fname, header=0, sep='\s+')
    # cavity_info = config_infos[config_infos['cavity_name'] == cavity_name]
    section = cavity_infos['section'][cavity_name]
    # section = cavity_info['section'].values[0]
    cavity = get_physic_amp(db, cavity_name, section)
    if not cavity:
        raise HTTPException(status_code=403, detail="没有上传lattice")
    physics_amp = cavity.amp
    await cache.set('cavity_name', cavity_name)
    await cache.set('physics_amp', physics_amp)

    amp_limit = pv_controller.get_cavity_amp_limit()
    amp_limit_item = {}
    amp_limit_item['name'] = cavity.cavity_name
    amp_limit_item['epk'] = amp_limit
    await cache.set('amp_limit', amp_limit)

    log_epk_item(db, amp_limit_item)
    return {
        "code": 20000,
        "physics_amp": physics_amp,
        "amp_limit": amp_limit
    }

@router.post('/commissioning/phasescan/phase-set',
             dependencies=[Depends(JWTBearer())])
async def phase_set(data: PhaseScanInfo,
                    cache: aioredis.Redis = Depends(fastapi_plugins.depends_redis)):
    #bypass_cavities = data.bypass_cavities
    for cavity_name in data.lattice:
        pv_controller.set_cavity_amp(cavity_name, data.lattice[cavity_name]['amp'])
        pv_controller.set_cavity_phase(cavity_name, data.lattice[cavity_name]['phase'])
        if float(data.lattice[cavity_name]['amp']) < 0.01: #or cavity_name in bypass_cavities:
            pv_controller.set_cavity_bypass(cavity_name, 1)
        else:
            pv_controller.set_cavity_bypass(cavity_name, 0)
    await asyncio.sleep(data.cavity_res_time)
    bpm1_vals = []
    bpm2_vals = []

    harm_index = 0 if data.bpm_harm == 'single' else 1
    for _ in range(data.bpm_read_num):
        bpm1_val = pv_controller.pvs_one_cavity[f'bpm{data.bpm_index+1}_pv'][harm_index].get()
        bpm2_val = pv_controller.pvs_one_cavity['bpm2_pv'][harm_index].get()
        bpm1_vals.append(bpm1_val)
        bpm2_vals.append(bpm2_val)
        await asyncio.sleep(data.bpm_read_sep)

    bpm1_val = np.average(bpm1_vals)
    bpm1_err = np.std(bpm1_vals)
    bpm2_val = np.average(bpm2_vals)
    bpm2_err = np.std(bpm2_vals)
    await cache.lpush('rf_phases', data.rf_phase)
    await cache.lpush('bpm1_phases', bpm1_val.item())
    await cache.lpush('bpm1_errors', bpm1_err.item())
    await cache.lpush('bpm2_phases', bpm2_val.item())
    await cache.lpush('bpm2_errors', bpm2_err.item())

    return {
        'code': 20000,
        'point1': dict(bpm_phase=bpm1_val, err=bpm1_err),
        'point2': dict(bpm_phase=bpm2_val, err=bpm2_err)
    }


@router.get('/commissioning/phasescan/get-status',
            dependencies=[Depends(JWTBearer())])
async def get_status():
    if not pv_controller.get_cavity_ready():
        return dict(code=600, message="腔体未准备好")
    if not pv_controller.get_current_ready():
        return dict(code=600, message="束流未准备好")
    if not pv_controller.get_orbit_ready():
        return dict(code=600, message="束流轨道偏离超过5mm")
    return dict(code=20000)


@router.post('/commissioning/phasescan/finish',
             dependencies=[Depends(JWTBearer())])
async def finish(data: CavityFinished,
                 cache: aioredis.Redis = Depends(fastapi_plugins.depends_redis)):
    pv_controller.finished.put(json.dumps({data.caity_name: data.finished}))
    #await cache.lpush('cavity_finished', data.cavity_name)
    return dict(code=20000)

@router.post('/commissioning/phasescan/set-mode',
             dependencies=[Depends(JWTBearer())])
def set_mode(data: CavityModel):
    #config_fname = basedir.joinpath('resources', 'config.txt')
    #config_infos = pd.read_csv(config_fname, header=0, sep='\s+')
    #cavities = config_infos['cavity_name'].to_list()
    #start_cavity_idx = cavities.index(data.cavity_name)
    #for i, cavity_name in enumerate(cavities):
    #    finished = False
        #if i >= start_cavity_idx:
        #    finished = False
    #    pv_controller.finished.put(json.dumps({cavity_name: finished}))
    pv_controller.mode.put(0x020C0)
    return dict(code=20000)

@router.post('/commissioning/phasescan/curve-fit',
             dependencies=[Depends(JWTBearer())])
async def curve_fit(data: CurveFitInfo,
                    cache: aioredis.Redis = Depends(fastapi_plugins.depends_redis)):
    cavity_name = data.cavity_name
    synch_phase_fname = basedir.joinpath('resources', 'synch_phases.txt')
    df = pd.read_csv(synch_phase_fname, header=0, sep=r'\s+')
    synch_phase = df[df['cavity_name'] == cavity_name]['synch_phase'].item()
    bpm_harm = data.bpm_harm

    config_fname = basedir.joinpath('resources', 'config.txt')
    config_infos = pd.read_csv(config_fname, header=0, sep='\s+')
    cavity_info = config_infos[config_infos['cavity_name'] == cavity_name]

    payload = {'distance': cavity_info[f'distance{data.bpm_index+1}'].item(),
               'field_name': cavity_info['field_name'].item() + '.txt',
               'sync_phase': synch_phase,
               'freq': 162.5e6,
               'bpm_harm': bpm_harm,
               'bpm_polarity': 1,
               'Epk_ref': cavity_info['Epk_ref'].item(),
               'rf_direction': cavity_info['rf_direction'].item()
               }

    payload = {**payload, **data.dict()}
    fit_obj = PhaseFit(payload)
    fit_result = fit_obj.fit()
    await cache.set('synch_phase', synch_phase)
    await cache.set('rf_amp', fit_result['amp'].item())
    await cache.set('rf_phase', fit_result['rf_phase'].item())
    await cache.set('energy', fit_result['w_out'].item())
    # scan_data = dict((key, value) for key, value in data.dict()
    #                 if key in ['cavity_phases', 'bpm_phases'])
    return dict(code=20000, **fit_result)


@router.post('/commissioning/phasescan/smoothing',
             dependencies=[Depends(JWTBearer())])
async def smoothing(data: SmoothData):
    return dict(code=20000, **smooth_data(**data.dict()))


'''
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor(1)
future = executor.submit(long_task)
async_function = sync_to_async(long_task, thread_sensitive=False)
#result = await long_task()
result = await async_function

return jsonify(
    {
        'result': result[0]
    }
)
'''
