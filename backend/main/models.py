from .factory import db, Base
from datetime import datetime, timedelta
import json

class Snapshot(db.Model):
    __tablename__ = 'snapshots'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    amps = db.relationship('Amp', backref='snapshot')
    phases = db.relationship('Phase', backref='snapshot')
    magnets = db.relationship('SnapshotMagnet', backref='snapshot')
    bpms = db.relationship('BPM', backref='snapshot')

    def to_json(self):
        json_snapshot = {}
        categories = {
            'amps': self.amps,
            'phases': self.phases,
            'magnets': self.magnets,
            'bpms': self.bpms
        }
        for c in categories:
            json_snapshot[c] = {}
            for item in categories[c]:
                json_item = item.to_json()
                json_snapshot[c][json_item['name']] = json_item['val']
        return json_snapshot

    def __repr__(self):
        return 'Snapshot {}'.format(self.id)


class BPM(db.Model):
    __tablename__ = 'bpms'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))
    val = db.Column(db.String(32))
    snapshot_id = db.Column(db.Integer, db.ForeignKey('snapshots.id'))

    def to_json(self):
        json_bpm = {
            'name': self.name,
            'val': self.val
        }
        return json_bpm

    def __repr__(self):
        return self.name


class Amp(db.Model):
    __tablename__ = 'amps'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))
    val = db.Column(db.String(32))
    snapshot_id = db.Column(db.Integer, db.ForeignKey('snapshots.id'))

    def to_json(self):
        json_amp = {
            'name': self.name,
            'val': self.val
        }
        return json_amp

    def __repr__(self):
        return self.name


class Phase(db.Model):
    __tablename__ = 'phases'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))
    val = db.Column(db.String(32))
    snapshot_id = db.Column(db.Integer, db.ForeignKey('snapshots.id'))

    def to_json(self):
        json_phase = {
            'name': self.name,
            'val': self.val
        }
        return json_phase

    def __repr__(self):
        return self.name


class SnapshotMagnet(db.Model):
    __tablename__ = 'snapshot_magnets'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))
    val = db.Column(db.String(32))
    snapshot_id = db.Column(db.Integer, db.ForeignKey('snapshots.id'))

    def to_json(self):
        json_magnet = {
            'name': self.name,
            'val': self.val
        }
        return json_magnet

    def __repr__(self):
        return self.name


class Operation(db.Model):
    __tablename__ = 'operations'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    description = db.Column(db.String(1024))
    magnets = db.relationship('Magnet', backref='operation')
    cavities = db.relationship('Cavity', backref='operation')

    def __repr__(self):
        return '<Operation {}>'.format(self.timestamp)


class Magnet(db.Model):
    __tablename__ = 'magnets'
    id = db.Column(db.Integer, primary_key=True)
    magnet_name = db.Column(db.String(64))
    section_name = db.Column(db.String(64))
    value = db.Column(db.String(64))
    operation_id = db.Column(db.Integer, db.ForeignKey('operations.id'))

    def __repr__(self):
        return '<Magnet {} {}>'.format(self.section_name, self.magnet_name)


class Cavity(db.Model):
    __tablename__ = 'cavities'
    id = db.Column(db.Integer, primary_key=True)
    cavity_name = db.Column(db.String(64))
    section_name = db.Column(db.String(64))
    amp = db.Column(db.String(64))
    phase = db.Column(db.String(64))
    operation_id = db.Column(db.Integer, db.ForeignKey('operations.id'))

    def __repr__(self):
        return '<Cavity {} {}>'.format(self.section_name, self.cavity_name)


class Timing(db.Model):
    __tablename__ = 'timing'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    dutyfactor = db.Column(db.Float(16))
    times = db.Column(db.Float(16))
    acct1 = db.Column(db.Float(16))
    acct2 = db.Column(db.Float(16))
    acct3 = db.Column(db.Float(16))
    acct4 = db.Column(db.Float(16))

    def __repr__(self):
        return 'Timing at {}'.format(self.timestamp)

    def to_json(self):
        return {
            'timestamp': self.timestamp + timedelta(hours=8),
            'duty_factor': self.dutyfactor,
            'beam_time': self.times / 3600,
            'acct1': self.acct1,
            'acct2': self.acct2,
            'acct3': self.acct3,
            'acct4': self.acct4
        }

class Task(Base):
    __tablename__ = 'task'
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    task_type = db.Column(db.String(64))
    name = db.Column(db.String(64))
    description = db.Column(db.String(64))
    task_level = db.Column(db.Integer, default=-1)
    skippable = db.Column(db.Boolean, unique=False, default=True)
    interactive = db.Column(db.Boolean, unique=False, default=True)
    parallelizable = db.Column(db.Boolean, default=False)
    user_code = db.Column(db.String(32), default="")
    children = db.relationship('Task',
                               backref=db.backref('parent', remote_side=[id]))

    @staticmethod
    def insert_tasks():
        with open('sequencer/task_data.json') as f:
            data = json.load(f)
        for task_name in data:
            if data[task_name]["task_type"] == "seq":
                sequence = Task(
                    task_type="seq",
                    name=data[task_name]["name"],
                    description=data[task_name]["description"],
                    task_level=0,
                    children=Task.create_sequence(data, task_name, task_level=1)
                )
                db.session.add(sequence)
        db.session.commit()

    @staticmethod
    def create_sequence(data, sequence_name, task_level):
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

    def __repr__(self):
        return self.name