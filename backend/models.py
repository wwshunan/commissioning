from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship, backref
from .database import Base
import os
from datetime import datetime

basedir = os.path.dirname(os.path.abspath(__file__))

class Snapshot(Base):
    __tablename__ = 'snapshots'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)
    subject = Column(String(256))
    particle_type = Column(String(32))
    current = Column(Float(16))
    energy = Column(Float(16))
    amps = relationship('Amp', backref='snapshot', cascade="all, delete-orphan")
    phases = relationship('Phase', backref='snapshot', cascade="all, delete-orphan")
    magnets = relationship('SnapshotMagnet', backref='snapshot', cascade="all, delete-orphan")
    bpms = relationship('BPM', backref='snapshot', cascade="all, delete-orphan")

    def to_json(self):
        json_snapshot = {}
        categories = {
            'AMP': self.amps,
            'PHASE': self.phases,
            'MAGNET': self.magnets,
            'DIAG': self.bpms
        }
        for c in categories:
            json_snapshot[c] = {}
            for item in categories[c]:
                json_item = item.to_json()
                if c == 'MAGNET':
                    assigned_val = json_item['set_val'], json_item['rb_val']
                else:
                    assigned_val = json_item['val']
                json_snapshot[c][json_item['name']] = assigned_val
            if not json_snapshot[c]:
                json_snapshot.pop(c)
        return json_snapshot

    def __repr__(self):
        return 'Snapshot {}'.format(self.id)

class BPM(Base):
    __tablename__ = 'bpms'
    id = Column(Integer, primary_key=True)
    name = Column(String(32))
    val = Column(Float(32))
    snapshot_id = Column(Integer, ForeignKey('snapshots.id'))

    def to_json(self):
        json_bpm = {
            'name': self.name,
            'val': self.val
        }
        return json_bpm

    def __repr__(self):
        return self.name

class Amp(Base):
    __tablename__ = 'amps'
    id = Column(Integer, primary_key=True)
    name = Column(String(32))
    val = Column(Float(32))
    snapshot_id = Column(Integer, ForeignKey('snapshots.id'))

    def to_json(self):
        json_amp = {
            'name': self.name,
            'val': self.val
        }
        return json_amp

    def __repr__(self):
        return self.name

class Phase(Base):
    __tablename__ = 'phases'
    id = Column(Integer, primary_key=True)
    name = Column(String(32))
    val = Column(Float(32))
    snapshot_id = Column(Integer, ForeignKey('snapshots.id'))

    def to_json(self):
        json_phase = {
            'name': self.name,
            'val': self.val
        }
        return json_phase

    def __repr__(self):
        return self.name

class SnapshotMagnet(Base):
    __tablename__ = 'snapshot_magnets'
    id = Column(Integer, primary_key=True)
    name = Column(String(32))
    set_val = Column(Float(32))
    rb_val = Column(Float(32))
    snapshot_id = Column(Integer, ForeignKey('snapshots.id'))

    def to_json(self):
        json_magnet = {
            'name': self.name,
            'set_val': self.set_val,
            'rb_val': self.rb_val
        }
        return json_magnet

    def __repr__(self):
        return self.name

class Lattice(Base):
    __tablename__ = 'lattices'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)
    magnets = relationship('Magnet', backref='lattice')
    cavities = relationship('Cavity', backref='lattice')

class Magnet(Base):
    __tablename__ = 'magnets'
    id = Column(Integer, primary_key=True)
    magnet_name = Column(String(64))
    section_name = Column(String(64))
    value = Column(String(64))
    lattice_id = Column(Integer, ForeignKey('lattices.id'))

class Cavity(Base):
    __tablename__ = 'cavities'
    id = Column(Integer, primary_key=True)
    cavity_name = Column(String(64))
    section_name = Column(String(64))
    amp = Column(Float(32))
    phase = Column(Float(32))
    lattice_id = Column(Integer, ForeignKey('lattices.id'))

class Timing(Base):
    __tablename__ = 'timing'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)
    dutyfactor = Column(Float(16))
    times = Column(Float(16))
    acct1 = Column(Float(16))
    acct2 = Column(Float(16))
    acct3 = Column(Float(16))
    acct4 = Column(Float(16))

class Task(Base):
    __tablename__ = 'task'
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('task.id'))
    task_type = Column(String(64))
    name = Column(String(64))
    description = Column(String(64))
    task_level = Column(Integer, default=-1)
    skippable = Column(Boolean, unique=False, default=True)
    interactive = Column(Boolean, unique=False, default=True)
    parallelizable = Column(Boolean, default=False)
    user_code = Column(String(32), default="")
    children = relationship('Task', backref=backref('parent', remote_side=[id]))

class CavityEpeak(Base):
    __tablename__ = 'cavity_epk'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    epk = Column(Float(32))
    #log_id = Column(Integer, ForeignKey('cavity_epk_log.id'))

#class CavityEpeakLog(Base):
#    __tablename__ = 'cavity_epk_log'
#    id = Column(Integer, primary_key=True)
#    #author = Column(String)
#    timestamp = Column(DateTime, index=True, default=datetime.utcnow)
#    epks = relationship('CavityEpeak', backref='cavity_epk_log')

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

class ScanData(Base):
    __tablename__ = 'scan_data'
    id = Column(Integer, primary_key=True)
    rf_phase = Column(Float(16))
    bpm1_phase = Column(Float(16))
    bpm2_phase = Column(Float(16))
    bpm1_error = Column(Float(16))
    bpm2_error = Column(Float(16))
    cavity_id = Column(Integer, ForeignKey('phase_scan_log.id'))

class PhasescanLog(Base):
    __tablename__ = 'phase_scan_log'
    id = Column(Integer, primary_key=True)
    cavity_name = Column(String(32))
    start_time = Column(DateTime, index=True, default=datetime.utcnow)
    physics_amp = Column(Float(32))
    rf_amp = Column(Float(32))
    synch_phase = Column(Float(32))
    rf_phase = Column(Float(32))
    bpm_phase_check = Column(Float(32))
    bpm1_name = Column(String(32))
    bpm2_name = Column(String(32))
    energy = Column(Float(32))
    scan_data = relationship('ScanData', backref='phase_scan_log')





