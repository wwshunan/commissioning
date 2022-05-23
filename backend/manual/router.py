from fastapi import APIRouter, Depends
from ..dependencies import JWTBearer
from pathlib import Path

router = APIRouter()
basedir = Path(__file__).resolve().parent

@router.get('/commissioning/get-manual',
            dependencies=[Depends(JWTBearer())])
async def get_manual():
    fname = basedir.joinpath('resources', 'manual.txt')
    with open(fname) as f:
        data = f.read()
    return {
        'code': 20000,
        'data': data
    }
