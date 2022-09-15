from re import S
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..dependencies import JWTBearer, get_db
from ..services.pv_handler import PhaseScanPVController
from ..services.worker import q
from ..schemas import  Id
from pathlib import Path
from ..crud import get_sequences, fetch_sequence
from .worker import TaskExecutor

router = APIRouter()
basedir = Path(__file__).resolve().parent
pv_controller = PhaseScanPVController()
task_executor = TaskExecutor(q)

@router.get('/commissioning/sequencer/load-sequences',
            dependencies=[Depends(JWTBearer())])
def load_sequences(db: Session = Depends(get_db)):
    sequences = get_sequences(db)
    sequences.pop(1)
    return {
        'code': 20000,
        'sequences': sequences
    }

@router.post('/commissioning/sequencer/init-sequence',
             dependencies=[Depends(JWTBearer())])
def sequence_init(data: Id, db: Session = Depends(get_db)):
    seq = fetch_sequence(db, data.id)
    task_executor.initialize_sequence(seq)
    return {
        'code': 20000,
    }

@router.get('/commissioning/sequencer/{task_id}',
            dependencies=[Depends(JWTBearer())])
def get_status(task_id: str):
    task = q.fetch_job(task_id)
    if task:
        #if 'word' in task.meta:
        #    print(task.meta['word'])
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

@router.post('/commissioning/sequencer/execute',
             dependencies=[Depends(JWTBearer())])
def execute():
    tasks = task_executor.execute_sequence()
    return {
        'code': 20000,
        'tasks': [{'id': e['id'], 'task': e['task'].get_id()} for e in tasks]
    }

@router.post('/commissioning/sequencer/step',
             dependencies=[Depends(JWTBearer())])
def step(task: Id):
    task = task_executor.execute_task(task.id)
    return {
        'code': 20000,
        'tasks': [{'id': task['id'], 'task': task['task'].get_id()}]
    }
