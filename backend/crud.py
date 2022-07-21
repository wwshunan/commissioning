from sqlalchemy.orm import Session
from .models import (Snapshot, Timing, Task, Magnet, Cavity, PhasescanLog, ScanData, 
                     CavityEpeak, User, Lattice, Amp, Phase, SnapshotMagnet, BPM)
from datetime import datetime
from sqlalchemy import desc, and_
from epics import PV
from dateutil import tz
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

models = {
    'AMP': Amp,
    'PHASE': Phase,
    'MAGNET': SnapshotMagnet,
    'DIAG': BPM
}

tolerances = {
    'phase': 0.2,
    'amp': 0.2,
    'magnet': 0.3,
    'x': 0.3,
    'y': 0.3,
    'p': 2
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
            item_label = k[:-1]
            item[item_label] = scan_data[k][i]
        raw_data = ScanData(**item, phase_scan_log=cavity_log)
        db.add(raw_data)
    db.commit()

def store_element_values(source, db, parent, child=None):
    for item in source:
        (key, val), = item.items()
        if key in ['DIAG', 'MAGNET', 'AMP', 'PHASE']:
            child = models[key]
            store_element_values(val, db, parent, child)
        elif not isinstance(val, list):
            if isinstance(val, tuple):
                snapshot_item = child(
                    name=key,
                    set_val=val[0],
                    rb_val=val[1],
                    snapshot=parent
                )
            else:
                snapshot_item = child(
                    name=key,
                    val=val,
                    snapshot=parent
                )
            db.add(snapshot_item)
        else:
            store_element_values(val, db, parent, child)


def save_snapshot(db: Session, particle_type, current, energy,
                  subject, source):
    if source:
        snapshot = Snapshot(particle_type=particle_type, current=current,
                            energy=energy, subject=subject)
        db.add(snapshot)
        store_element_values(source, db, snapshot)
        db.commit()

def remove_snapshot(db: Session, snapshot_id: int): 
    snapshot = db.query(Snapshot).filter(Snapshot.id == snapshot_id).first()
    db.delete(snapshot)
    db.commit()

def acquire_snapshot(db: Session, begin_date: datetime, end_date: datetime):
    snapshots = db.query(Snapshot).filter(Snapshot.timestamp.between(begin_date, end_date)). \
        order_by(Snapshot.timestamp.desc()).all()
    results = []
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('China/Beijing')
    for snapshot in snapshots:
        result = {}
        result['id'] = snapshot.id
        utc = snapshot.timestamp.replace(tzinfo=from_zone)
        result['timestamp'] = utc.astimezone(to_zone).strftime('%Y-%m-%d %H:%M')
        result['energy'] = snapshot.energy
        result['particle_type'] = snapshot.particle_type
        result['current'] = snapshot.current
        result['subject'] = snapshot.subject
        results.append(result)

    return results

def restore_element_values(source, recover_data, key=None):
    for s in source:
        if s['id'].upper() in ['AMP', 'PHASE', 'MAGNET']:
            key = s['id'].upper()
        if key and s['id'] in recover_data[key]:
            recover_item = recover_data[key][s['id']]
            if isinstance(recover_item, tuple):
                pv_name = s['write_pv']
                pv_val = recover_item[0]
            else:
                pv_name = s['pv']
                pv_val = recover_item
            PV(pv_name).put(pv_val)
        elif 'children' in s:
            restore_element_values(s['children'], recover_data, key)


def restore_snapshot(db: Session, snapshot_id: int, source: dict):
    snapshot = db.query(Snapshot).filter(Snapshot.id==snapshot_id).first()
    stored_snapshot_data = snapshot.to_json()

    #snapshot_recover = {}
    #for key in stored_snapshot_data:
    #    if key in ['MAGNET', 'AMP', 'PHASE']:
    #        snapshot_recover.update(stored_snapshot_data[key])
    #print(snapshot_recover)
    restore_element_values(source, stored_snapshot_data)

def compare_snapshot(db: Session, snapshot_id: int, source: dict):
    snapshot = db.query(Snapshot).filter(Snapshot.id==snapshot_id).first()
    stored_snapshot_data = snapshot.to_json()
    #snapshot_ravel = {}
    #for key in stored_snapshot_data:
    #    snapshot_ravel.update(stored_snapshot_data[key])
    return get_diffs(source, stored_snapshot_data)

def get_diffs(source, old_data, key=None, tolerance=0):
    diff_dict = {}
    for s in source:
        if s['id'].upper() in models.keys():
            key = s['id'].upper()
        if s['id'] in tolerances:
            tolerance = tolerances[s['id']]
        if key in old_data and s['id'] in old_data[key]:
            old_item = old_data[key][s['id']]
            if isinstance(old_item, tuple):
                old_set_val, old_rb_val = old_item
                new_set_val = PV(s['write_pv']).get()
                new_rb_val = PV(s['rb_pv']).get()
                if abs(new_set_val-old_set_val) > tolerance:
                    diff_dict[s['label']+'-WR'] = old_set_val
                if abs(new_rb_val-old_rb_val) > tolerance:
                    diff_dict[s['label']+'-RB'] = old_rb_val
            else:
                new_val = PV(s['pv']).get()
                if abs(new_val-old_item) > tolerance:
                    diff_dict[s['id']] = old_item
        elif 'children' in s:
            diff_dict.update(get_diffs(s['children'], old_data, key, tolerance))
    return diff_dict


