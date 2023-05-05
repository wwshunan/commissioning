from typing import List, Union, Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

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

class BpmLimitModel(BaseModel):
    bpm_sum_limit: float
    orbit_offset_limit: float

class PhaseScanInfo(BaseModel):
    bpm_mode: str
    lattice: dict
    rf_phase: float
    cavity_res_time: float
    bpm_read_num: int
    bpm_read_sep: float
    bpm_harm: str
    bpm_index: int
    orbit_offset_limit: float
    bpm_sum_limit: float

class CurveFitInfo(BaseModel):
    cavity_phases: List[float]
    bpm_phases: Union[List[float], List[List[float]]]
    Win: float
    start_phase: float
    m: float
    q: int
    cavity_name: str
    bpm_mode: str
    bpm_harm: int
    bpm_index: int

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
    keys: List[str]
    rm_step: float
    sc_step: float
    rm_lim: float
    sc_lim: float
    alpha: float

class CorrectorStrength(BaseModel):
    keys: List[str]
    strength: list

class OneCorrector(BaseModel):
    name: Optional[str]
    set_pv: str
    get_pv: Optional[str]
    step: float
    limit: Optional[float]

class Correctors(BaseModel):
    section_data: dict
    step: float
    limit: float

class Snapshot(BaseModel):
    keys: List[str]
    particle_type: str
    energy: float
    current: float
    subject: str

class SnapshotAcquire(BaseModel):
    beginDate: datetime
    endDate: datetime

class HEBTMatch(BaseModel):
    target: str
    opti_param: str
    sample_num: int
    step: float
    max_iter: int
    freq: float
    ssfc_stop_current: float
    ssfc_modify_factor: float

class Orbit(BaseModel):
    section_data: dict

class SavedFile(BaseModel):
    filename: str

class SavedBpmVar(BaseModel):
    corr: str
    step: float
    bpm_names: List[str]
    bpm_var_xs: List[float]
    bpm_var_ys: List[float]

class Timing(BaseModel):
    timing_repeat: int
    timing_width: int

class Id(BaseModel):
    id: int
    kwargs: Optional[dict]

class Name(BaseModel):
    label: str
