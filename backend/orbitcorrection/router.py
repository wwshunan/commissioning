from fastapi import (APIRouter, Depends, UploadFile, File, Form,
                     WebSocket, HTTPException, Security)
from rq import Queue, Connection
from ..services.worker import conn
from ..dependencies import JWTBearer, get_db
from ..services.pv_handler import PhaseScanPVController
from ..schemas import CorrectInfo, CorrectorStrength
from .worker import create_task, set_corrector_strength
import pandas as pd
from pathlib import Path
from .orbit import Orbit, MeasureResponseMatrix, ResponseMatrix, Corrector
import fastapi_plugins
import aioredis
import redis
import json

router = APIRouter()
basedir = Path(__file__).resolve().parent
pv_controller = PhaseScanPVController()


@router.get('/commissioning/orbit-correction/get-config',
            dependencies=[Depends(JWTBearer())])
async def get_config():
    fname = basedir.joinpath('resources', 'config.json')
    with open(fname) as f:
        data = json.load(f)
    return {
        'code': 20000,
        'data': data
    }

@router.post('/commissioning/orbit-correction/compute-strength',
             dependencies=[Depends(JWTBearer())])
def compute_strength(data: CorrectInfo):
    params = (data.keys, data.rm_step, data.sc_step,
              data.rm_lim, data.sc_lim, data.alpha)
    with Connection(redis.from_url('redis://127.0.0.1:6379')):
        q = Queue()
        task = q.enqueue(create_task, *params, job_timeout=3000)
    return {
        'code': 20000,
        'task_id': task.get_id()
    }

@router.post('/commissioning/orbit-correction/set-strength',
             dependencies=[Depends(JWTBearer())])
def set_strength(data: CorrectorStrength):
    params = (data.keys, data.strength)
    with Connection(redis.from_url('redis://127.0.0.1:6379')):
        q = Queue()
        q.enqueue(set_corrector_strength, *params, job_timeout=3000)
    return {
        'code': 20000
    }


@router.get('/commissioning/orbit-correction/{task_id}',
            dependencies=[Depends(JWTBearer())])
def get_status(task_id: str):
    with Connection(redis.from_url('redis://127.0.0.1:6379')):
        q = Queue()
        task = q.fetch_job(task_id)
        if task:
            response_object = {
                "code": 20000,
                "data": {
                    "task_id": task.get_id(),
                    "task_status": task.get_status(),
                    "task_result": task.result,
                },
            }
            return response_object
        else:
            raise HTTPException(status_code=500, detail="正在进行轨道校正")

