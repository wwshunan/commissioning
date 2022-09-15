from fastapi import APIRouter, Depends, HTTPException
from ..services.worker import q
from ..dependencies import JWTBearer
from ..services.pv_handler import PhaseScanPVController
from pathlib import Path
from ..schemas import HEBTMatch
from ..hebt_match.worker import hebt_q_match

router = APIRouter()
basedir = Path(__file__).resolve().parent
pv_controller = PhaseScanPVController()

@router.post('/commissioning/hebt-match/matching',
             dependencies=[Depends(JWTBearer())])
def matching(data: HEBTMatch):
    params = (data.target, data.opti_param, data.freq, data.sample_num, data.ssfc_modify_factor,
              data.max_iter, data.ssfc_stop_current, data.step)
    task = q.enqueue(hebt_q_match, *params, job_timeout=3000)
    return {
        'code': 20000,
        'task_id': task.get_id()
    }

@router.get('/commissioning/hebt-match/{task_id}',
            dependencies=[Depends(JWTBearer())])
def get_status(task_id: str):
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
        raise HTTPException(status_code=500, detail="正在进行匹配")

@router.post('/commissioning/hebt-match/cancel/{task_id}',
             dependencies=[Depends(JWTBearer())])
def cancel(task_id: str):
    task = q.fetch_job(task_id)
    if task:
        task.meta['stop'] = True
        task.save()
    return {
        "code": 20000
    }