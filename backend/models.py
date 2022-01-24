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
    amps = relationship('Amp', backref='snapshot')
    phases = relationship('Phase', backref='snapshot')
    magnets = relationship('SnapshotMagnet', backref='snapshot')
    bpms = relationship('BPM', backref='snapshot')

class BPM(Base):
    __tablename__ = 'bpms'
    id = Column(Integer, primary_key=True)
    name = Column(String(32))
    val = Column(String(32))
    snapshot_id = Column(Integer, ForeignKey('snapshots.id'))

class Amp(Base):
    __tablename__ = 'amps'
    id = Column(Integer, primary_key=True)
    name = Column(String(32))
    val = Column(String(32))
    snapshot_id = Column(Integer, ForeignKey('snapshots.id'))

class Phase(Base):
    __tablename__ = 'phases'
    id = Column(Integer, primary_key=True)
    name = Column(String(32))
    val = Column(String(32))
    snapshot_id = Column(Integer, ForeignKey('snapshots.id'))

class SnapshotMagnet(Base):
    __tablename__ = 'snapshot_magnets'
    id = Column(Integer, primary_key=True)
    name = Column(String(32))
    val = Column(String(32))
    snapshot_id = Column(Integer, ForeignKey('snapshots.id'))

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





