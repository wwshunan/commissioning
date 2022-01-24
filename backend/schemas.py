from typing import List, Union, Optional
from pydantic import BaseModel, Field, EmailStr

class Task(BaseModel):
    id: int
    parent_id: int
    task_type: str
    name: str
    description: str
    task_level: int
    skippable: bool
    interactive: bool
    parallelizable: bool
    user_code: str
    children: List['Task']

class EnergyModel(BaseModel):
    tof: float = Field(..., gt=0)
    distance: float = Field(..., gt=0)
    mass: float = Field(..., gt=0)

class PhaseScanInfo(BaseModel):
    bpm_model: str
    lattice: dict
    #amp: List[float]
    #phase: List[float]
    #cavity_write_pv: str
    #cavity_rb_pv: str
    #cavity_ready_pv: str
    #bpm1_phase_pv: str
    #bpm2_phase_pv: str
    cavity_res_time: float
    bpm_read_num: int
    bpm_read_sep: float

class CurveFitInfo(BaseModel):
    cavity_phases: List[float]
    bpm_phases: Union[List[float], List[List[float]]]
    Win: float
    start_phase: float
    m: float
    q: int
    cavity_name: str
    bpm_model: str


class SmoothData(BaseModel):
    xs: List[float]
    ys: List[List[float]]
    errs: List[List[float]]
    step: float


class LoginModel(BaseModel):
    email: EmailStr
    password: str

class RegisterModel(LoginModel):
    username: str
    verify_code: str

class EmailSchema(BaseModel):
    email: List[EmailStr]

class CavityModel(BaseModel):
    cavity_name: str
    bpm_mode: Optional[str]

class SynchPhaseModel(BaseModel):
    lattice: dict

class CavityAmp(BaseModel):
    cavity_name: str
    amp: str

class CavityFinished(BaseModel):
    cavity_name: str
    finished: bool

class CorrectInfo(BaseModel):
    keys: List[int]
    rm_step: float
    sc_step: float
    rm_lim: float
    sc_lim: float
    alpha: float

class CorrectorStrength(BaseModel):
    strength: list

