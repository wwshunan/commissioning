from sqlalchemy.orm import Session
from .models import (Snapshot, Timing, Task, Magnet, Cavity, PhasescanLog,
                     ScanData, CavityEpeak, User, Lattice, )
from datetime import datetime
from sqlalchemy import desc, and_
import os
import json

db_maps = {
    'buncher1': 'cavity 0',
    'buncher2': 'cavity 1',
    'cm1-1': 'cavity 0',
    'cm1-2': 'cavity 1',
    'cm1-3': 'cavity 2',
    'cm1-4': 'cavity 3',
    'cm1-5': 'cavity 4',
    'cm1-6': 'cavity 5',
    'cm2-1': 'cavity 0',
    'cm2-2': 'cavity 1',
    'cm2-3': 'cavity 2',
    'cm2-4': 'cavity 3',
    'cm2-5': 'cavity 4',
    'cm2-6': 'cavity 5',
    'cm3-1': 'cavity 0',
    'cm3-2': 'cavity 1',
    'cm3-3': 'cavity 2',
    'cm3-4': 'cavity 3',
    'cm3-5': 'cavity 4',
    'cm3-6': 'cavity 5',
    'cm4-1': 'cavity 0',
    'cm4-2': 'cavity 1',
    'cm4-3': 'cavity 2',
    'cm4-4': 'cavity 3',
    'cm4-5': 'cavity 4',
}

basedir = os.path.dirname(os.path.abspath(__file__))


def get_snapshot(db: Session):
    snapshot = db.query(Snapshot).order_by(Snapshot.timestamp.desc()).limit(1).first()
    return snapshot


def get_beam_time(db: Session, begin_time: datetime, end_time: datetime):
    data = db.query(Timing).filter(
        Timing.timestamp >= begin_time).filter(Timing.timestamp <= end_time).all()
    return data


def create_sequence(data: dict, sequence_name: str, task_level: int):
    children = []
    tasks = data[sequence_name]["tasks"]
    next_task_level = task_level + 1
    for task in tasks:
        task_id = task["task_id"]
        child = data[task_id]
        if child["task_type"] == "task":
            children.append(Task(
                task_type="task",
                name=child["name"],
                description=child["description"],
                skippable=child["skippable"],
                interactive=child["interactive"],
                user_code=child["user_code"],
            ))
        else:
            sequence = Task(
                task_type="seq",
                name=child["name"],
                description=child["description"],
                task_level=task_level,
                children=Task.create_sequence(data, task_id, next_task_level)
            )
            children.append(sequence)
    return children


def add_tasks(db: Session):
    with open(os.path.join(basedir, 'sequencer/task_data.json')) as f:
        data = json.load(f)
    for task_name in data:
        if data[task_name]["task_type"] == "seq":
            sequence = Task(
                task_type="seq",
                name=data[task_name]["name"],
                description=data[task_name]["description"],
                task_level=0,
                children=create_sequence(data, task_name, task_level=1)
            )
            db.add(sequence)
    db.commit()


def log_lattice(db: Session, lattice_data: dict):
    lattice = Lattice()
    db.add(lattice)
    for section_name, section in lattice_data.items():
        for element_kind, elements in section.items():
            for i, el in enumerate(elements):
                if element_kind == 'magnets':
                    magnet_name = f'magnet {i}'
                    magnet_value = el
                    magnet = Magnet(magnet_name=magnet_name, section_name=section_name,
                                    value=magnet_value, lattice=lattice)
                    db.add(magnet)
                else:
                    cavity_name = f"cavity {i}"
                    cavity_values = el
                    cavity = Cavity(cavity_name=cavity_name, section_name=section_name,
                                    amp=cavity_values['amp'], phase=cavity_values['phase'],
                                    lattice=lattice)
                    db.add(cavity)
    db.commit()


#def create_epk_log(db: Session, epk_data: dict):
#    epk_log = CavityEpeakLog()
#    # epk_log = CavityEpeakLog(author=epk_data.author)
#    db.add(epk_log)
#
#    for item in epk_data['epks']:
#        cavity_epk = CavityEpeak(name=item['name'], epk=item['epk'], cavity_epk_log=epk_log)
#        db.add(cavity_epk)
#    db.commit()

def log_epk_item(db: Session, epk_data: dict):
    cavity_epk = CavityEpeak(name=epk_data['name'], epk=epk_data['epk'])
    db.add(cavity_epk)
    db.commit()

def get_user(db: Session, email: str):
    user = db.query(User).filter(User.email == email).first()
    return user


def put_user(db: Session, username: str, password: str, email: str):
    user = User(username=username, password=password, email=email)
    db.add(user)
    db.commit()


def get_physic_amp(db: Session, cavity_name: str, section: str):
    newest_lattice = db.query(Lattice).order_by(desc(Lattice.timestamp)).first()
    for cavity in newest_lattice.cavities:
        if (cavity.cavity_name == db_maps[cavity_name]
                and cavity.section_name == section):
            return cavity
    #return db.query(Cavity).join(Lattice). \
    #    filter(Lattice.timestamp == newest_lattice.timestamp). \
    #    filter(and_(Cavity.cavity_name == db_maps[cavity_name], Cavity.section_name == section)). \
    #    first()


def get_amp_limt(db: Session, cavity_name: str):
    newest_epk = db.query(CavityEpeakLog). \
        order_by(desc(CavityEpeakLog.timestamp)).first()
    for epk in newest_epk.epks:
        if (epk.name == cavity_name):
            return epk
    #return newest_epk.epks.filter(CavityEpeak.name == cavity_name).first()

def create_phase_scan_log(db: Session, general_info: dict, scan_data: dict):
    cavity_log = PhasescanLog(**general_info)
    db.add(cavity_log)

    data_len = len(scan_data['rf_phases'])
    for i in range(data_len):
        item = {}
        for k in scan_data:
            item[k] = scan_data[k][i]
        raw_data = ScanData(**item, phase_scan_log=cavity_log)
        db.add(raw_data)
    db.commit()
