from fastapi import (APIRouter, Depends, UploadFile, File, Form,
                     WebSocket, HTTPException, Security)
from epics import PV
from sqlalchemy.orm import Session
from ..services.worker import conn
from ..dependencies import JWTBearer, get_db
from ..services.pv_handler import PhaseScanPVController
from pathlib import Path
from ..schemas import Snapshot, SnapshotAcquire, SnapshotId
from .snapshot import get_element_values
from ..crud import save_snapshot, acquire_snapshot, restore_snapshot, compare_snapshot, remove_snapshot
import json

router = APIRouter()
basedir = Path(__file__).resolve().parent
pv_controller = PhaseScanPVController()

@router.get('/commissioning/snapshot/get-config',
            dependencies=[Depends(JWTBearer())])
async def get_config():
    fname = basedir.joinpath('resources', 'config.json')
    with open(fname) as f:
        data = json.load(f)
    return {
        'code': 20000,
        'data': data
    }

@router.post('/commissioning/snapshot/save',
             dependencies=[Depends(JWTBearer())])
async def save(data: Snapshot,
               db: Session = Depends(get_db)):
    fname = basedir.joinpath('resources', 'config.json')
    with open(fname) as f:
        source = json.load(f)
    snapshot_list = []
    get_element_values(snapshot_list, source, data.keys)
    save_snapshot(db, data.particle_type, data.current,
                  data.energy, data.subject, snapshot_list)

    return dict(code=20000, message="快照已保存")

@router.post('/commissioning/snapshot/acquire',
             dependencies=[Depends(JWTBearer())])
async def acquire(date_times: SnapshotAcquire,
                  db: Session = Depends(get_db)):
    results = acquire_snapshot(db, date_times.beginDate, date_times.endDate)
    return {
        'code': 20000,
        'data': results
    }

@router.post('/commissioning/snapshot/compare',
             dependencies=[Depends(JWTBearer())])
async def compare(data: SnapshotId,
                  db: Session = Depends(get_db)):
    fname = basedir.joinpath('resources', 'config.json')
    with open(fname) as f:
        source = json.load(f)
    diffs = compare_snapshot(db, data.id, source)
    return {
        'code': 20000,
        'data': diffs
    }


@router.post('/commissioning/snapshot/remove',
             dependencies=[Depends(JWTBearer())])
async def remove(data: SnapshotId,
                 db: Session = Depends(get_db)):
    remove_snapshot(db, data.id)
    return {
        'code': 20000
    }

@router.post('/commissioning/snapshot/restore',
             dependencies=[Depends(JWTBearer())])
async def restore(data: SnapshotId,
                  db: Session = Depends(get_db)):
    fname = basedir.joinpath('resources', 'config.json')
    with open(fname) as f:
        source = json.load(f)
    restore_snapshot(db, data.id, source)
    return {
        'code': 20000,
    }

