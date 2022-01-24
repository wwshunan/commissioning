from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from ..dependencies import get_db
from typing import List
from .epk import epk_dict
router = APIRouter()

@router.post('/commissioning/cavity-epk')
async def epk_upload(db: Session = Depends(get_db),
                     #author: str = Form(...),
                     file: UploadFile = File(...)) -> str:
                     #epk_file: UploadFile = File(...)) -> str:
    #epk_data = epk_dict(author, epk_file.file)
    #create_epk_log(db, epk_data)
    print(file)
    return 'SUCCESS'
