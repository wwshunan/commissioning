from werkzeug.utils import secure_filename
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from backend.lattice import load_lattice, generate_info, set_lattice, set_sync_phases
from backend.snapshot_log import get_pv_values, checkout
#from backend.sequencer.sequence import Sequence
#from backend.sequencer.callable_task import CallableTask
from sequencer.task_impl import ADSTask, ADSSequence
from sequencer.task_state import TaskState
from sequencer.priority_item import PrioritizedItem
from backend.sequencer.task_user_interface import TaskUserInterface
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy, declarative_base
from datetime import datetime, timedelta
from collections import OrderedDict
from flask_nameko import FlaskPooledClusterRpcProxy
from flask_redis import FlaskRedis
from urllib.parse import unquote
from flask_socketio import SocketIO, emit
from event_manager import *
import numpy as np
import os, time, json, importlib
import eventlet

app = Flask(__name__)

config = {
    "DEBUG": True,  # some Flask specific configs
    "CACHE_TYPE": "simple",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 0,
    "SQLALCHEMY_DATABASE_URI": 'sqlite:///lattice.db',
    "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    'JSON_SORT_KEYS': False,
    'NAMEKO_AMQP_URI': 'pyamqp://guest:guest@localhost'
}
app.config.from_mapping(config)
cache = Cache(app)
db = SQLAlchemy(app)
redis_client = FlaskRedis(app)
eventlet.monkey_patch()
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")
#rpc = FlaskPooledClusterRpcProxy(app)

Base = declarative_base()

CORS(app, resources=r'/*')

results = {
    'NOT_STARTED': "<span>NOT_STARTED</span>",
    'FINISHED': "<span style='color: green; '>FINISHED</span>",
    'FINISHED_FAULTY': "<span style='color: red; '>FINISHED_FAULTY</span>",
    'SKIPPED': "<span style='color: yellow; '>SKIPPED</span>",
}

event_manager = EventManager()
event_manager.start()

sequence_to_execute = None

class UserCode(TaskUserInterface):
    def __init__(self, task):
        self.module = 'sequencer.user_codes.tasks'
        self.task = task

    def execUserCode(self):
        mod = importlib.import_module(self.module)
        user_code = getattr(mod, self.task.user_code)
        try:
            result = user_code()
            status = TaskState.OK.name
        except:
            status = TaskState.FAILURE.name
        finally:
            socketio.emit('finished', {
                'status': status,
                'id': self.task.id,
                'name': self.task.name
            })
            return status

@socketio.on('connect')
def task_connect():
    print('connected!')

def remove_dict_null(data):
    copied_keys = tuple(data.keys())
    for key in copied_keys:
        if isinstance(data[key], dict) and data[key]:
            remove_dict_null(data[key])
        if not data[key]:
            data.pop(key)


@app.route('/lattice-upload', methods=['POST'])
def lattice_upload():
    f = request.files['file']
    f.save(unquote(f.filename))
    # f.save(secure_filename(unquote(f.filename)))
    lattice_data = load_lattice(unquote(f.filename))
    remove_dict_null(lattice_data)
    lattice_info = generate_info(lattice_data)
    cache.set('lattice_data', lattice_data)
    cache.set('lattice_info', lattice_info)
    return jsonify({
        'lattice': lattice_info
    })


@app.route('/lattice-setting', methods=['POST'])
def lattice_setting():
    post_data = request.get_json()
    lattice_data = cache.get('lattice_data')
    lattice_info = cache.get('lattice_info')
    set_lattice(lattice_data)
    set_sync_phases(lattice_data)
    if post_data['saveToDB']:
        operation = Operation(description=post_data['latticeDescription'])
        db.session.add(operation)
        for section_name, section in lattice_info.items():
            for element_type, element_collections in section.items():
                for element in element_collections:
                    if element_type in ['quad', 'sol']:
                        magnet_name = element
                        magnet_value = element_collections[element]
                        magnet = Magnet(magnet_name=magnet_name, section_name=section_name,
                                        value=magnet_value, operation=operation)
                        db.session.add(magnet)
                    else:
                        cavity_name = element
                        cavity_values = element_collections[element]
                        cavity = Cavity(cavity_name=cavity_name, section_name=section_name,
                                        amp=cavity_values['amp'], phase=cavity_values['phase'],
                                        operation=operation)
                        db.session.add(cavity)
        db.session.commit()
    resp = jsonify(success=True)
    return resp


@app.route('/lattice-query', methods=['POST'])
def lattice_query():
    section_names = ['MEBT', 'CM1', 'CM2', 'CM3', 'CM4', 'HEBT']
    post_data = request.get_json()
    start_date = datetime.strptime(post_data['startDate'], "%Y-%m-%dT%H:%M:%S.%fZ")
    to_date = datetime.strptime(post_data['toDate'], "%Y-%m-%dT%H:%M:%S.%fZ")
    operation_condition = Operation.query.filter(
        Operation.timestamp >= start_date).filter(Operation.timestamp <= to_date)

    operation_info = []
    operations = operation_condition.all()
    for op in operations:
        operation = OrderedDict()
        operation['timestamp'] = op.timestamp + timedelta(hours=8)
        lattice = OrderedDict()
        for name in section_names:
            lattice[name] = OrderedDict()
            lattice[name]['magnet'] = OrderedDict()
            lattice[name]['cavity'] = OrderedDict()
        for m in op.magnets:
            lattice[m.section_name]['magnet'][m.magnet_name] = m.value
        for cav in op.cavities:
            lattice[cav.section_name]['cavity'][cav.cavity_name] = \
                OrderedDict([('amp', cav.amp), ('phase', cav.phase)])
        remove_dict_null(lattice)
        operation['description'] = op.description
        operation['lattice'] = lattice
        operation_info.append(operation)

    resp = jsonify({
        'operations': operation_info
    })
    return resp


@app.route('/log/start', methods=['GET'])
def start_time_accumulate():
    interrupt_id, time_break_id = rpc.usage_time_service.start()
    cache.set('interrupt', interrupt_id)
    cache.set('time_break', time_break_id)
    with open('slaves/timing-id.txt', 'w') as fobj:
        fobj.write('{}\t{}\n'.format(interrupt_id, time_break_id))
    rpc.usage_time_service.accumulate_time.call_async(interrupt_id, time_break_id)
    return jsonify(status='Success')


@app.route('/log/stop', methods=["GET"])
def stop_time_accumulate():
    #time_break_id = cache.get('time_break')
    with open('slaves/timing-id.txt') as fobj:
        time_break_id = fobj.readlines()[0].split()[1]
    status = rpc.usage_time_service.stop(time_break_id)
    # usage_time = json.loads(usage_time)
    # usage_time = float(usage_time['0.0']['beam_time']) / 3600
    # return jsonify({'usage_time': round(usage_time, 3)})
    return status


@app.route('/log/interrupt', methods=["GET"])
def interrupt_timing():
    with open('slaves/timing-id.txt') as fobj:
        interrupt_id = fobj.readlines()[0].split()[0]
    usage_time = rpc.usage_time_service.interrupt(interrupt_id)
    usage_time = json.loads(usage_time)
    for duty_factor in usage_time:
        for acct in ['ACCT1', 'ACCT2', 'ACCT3', 'ACCT4']:
            if usage_time[duty_factor]['count'] == 0:
                usage_time[duty_factor][acct] = 0
            else:
                usage_time[duty_factor][acct] /= usage_time[duty_factor]['count']
        usage_time[duty_factor].pop('count')
        usage_time[duty_factor]['beam_time'] = round(usage_time[duty_factor]['beam_time'] / 3600, 3)

    return jsonify({'usage_time': usage_time})

@app.route('/log/time-query', methods=['POST'])
def time_query():
    post_data = request.get_json()
    start_date = datetime.strptime(post_data['startDate'], "%Y-%m-%dT")
    to_date = datetime.strptime(post_data['toDate'], "%Y-%m-%dT")
    query_condition = Timing.query.filter(
        Timing.timestamp >= start_date).filter(Timing.timestamp <= to_date)

    timing_info = []
    timings = query_condition.all()
    #timing_data = [datetime.strptime(t.timestamp, '')]
    for t in timings:
        print(type(t.timestamp))
        timing_info.append(t.to_json())
    print(timing_info)
    return jsonify({
        'usage_time': timing_info
    })


@app.route('/log/snapshot', methods=['POST'])
def snapshot():
    loop_num = 6
    data = request.get_json()
    selected_sections = data['selected_sections']
    cache.set('selected_sections', selected_sections)
    snapshots = {}
    for i in range(loop_num):
        pv_values = get_pv_values(selected_sections)
        print(pv_values)
        for k in pv_values:
            if k not in snapshots:
                snapshots[k] = {}
            for name in pv_values[k]:
                if name not in snapshots[k]:
                    snapshots[k][name] = []
                snapshots[k][name].append(pv_values[k][name])
        time.sleep(1)

    for k in snapshots:
        for name in snapshots[k]:
            snapshots[k][name] = np.average(snapshots[k][name])

    snapshot_record = Snapshot()
    db.session.add(snapshot_record)

    model_type = {
        'amps': Amp,
        'phases': Phase,
        'magnets': SnapshotMagnet,
        'bpms': BPM
    }

    for k in snapshots:
        for name in snapshots[k]:
            snapshot_item = model_type[k](
                name=name,
                val=snapshots[k][name],
                snapshot=snapshot_record
            )
            db.session.add(snapshot_item)
    db.session.commit()

    resp = jsonify(status='Success')
    return resp


@app.route('/log/snapshot-checkout', methods=['GET'])
def snapshot_checkout():
    newest_snapshot = Snapshot.query.order_by(
        Snapshot.timestamp.desc()
    ).limit(1).first()

    data = newest_snapshot.to_json()
    selected_sections = cache.get('selected_sections')
    diffs = checkout(data, selected_sections)
    return jsonify({
        'diffs': diffs
    })


def save_timing(timing_data):
    print(timing_data)
    for dutyfactor in timing_data:
        for acct in ['ACCT1', 'ACCT2', 'ACCT3', 'ACCT4']:
            if timing_data[dutyfactor]['count'] == 0:
                timing_data[dutyfactor][acct] = 0
            else:
                timing_data[dutyfactor][acct] /= timing_data[dutyfactor]['count']

        timing_item = Timing(
            dutyfactor=dutyfactor,
            times=timing_data[dutyfactor]['beam_time'],
            acct1=timing_data[dutyfactor]['ACCT1'],
            acct2=timing_data[dutyfactor]['ACCT2'],
            acct3=timing_data[dutyfactor]['ACCT3'],
            acct4=timing_data[dutyfactor]['ACCT4'],
        )
        db.session.add(timing_item)
    db.session.commit()

@app.route('/commissioning/task-stop', methods=['POST'])
def task_stop():
    stop_event = PrioritizedItem(0, 'stop')
    event_manager.send_task(stop_event)
    return jsonify({
        'status': 'OK'
    })

@app.route('/commissioning/task-step', methods=['POST'])
def task_step():
    task_id = request.get_json()['id']
    sequence = sequence_to_execute
    tasks = sequence.getFlattenedTaskList()
    manager = sequence.event_manager
    print(type(tasks))
    i = 0
    for t in tasks:
        if t.id == task_id:
            task = t
            if i < len(tasks) - 1:
                next_task_id = tasks[i+1].id
            else:
                next_task_id = tasks[i].id
            break
        i += 1
    task_item = PrioritizedItem(1, task.userCode.execUserCode)
    manager.send_task(task_item)
    socketio.emit('next_task', {
        'next_task_id': next_task_id
    })
    return jsonify({
        'stauts': 'OK'
    })

@app.route('/commissioning/sequence-init', methods=['POST'])
def sequence_init():
    global sequence_to_execute
    # EVENT_STARTUP = 'Event_Startup'
    # EVENT_FINISHED = 'Event_Finished'
    # event_manager.add_event_worker(EVENT_STARTUP, )
    sequence = request.get_json()
    seq = db.session.query(Task).filter(Task.id == sequence['id']).first()
    worker_num = 1
    if seq.parallelizable:
        worker_num = 5

    event_manager.set_worker_num = worker_num
    # executor = ThreadPoolExecutor(max_workers=worker_num)
    sequence = sequence_instantiate(seq, event_manager)
    sequence_to_execute = sequence
    return jsonify({
        'status': 'OK'
    })

@app.route('/commissioning/sequence-execute', methods=['POST'])
def sequence_execute():
    #sequence = sequence_instantiate(seq, executor)
    sequence = sequence_to_execute
    sequence.execUserCode()
    return jsonify({
        "status": "OK"
    })

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
                children=create_sequence(data, task_id, next_task_level)
            )
            children.append(sequence)
    return children

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
                children=create_sequence(data, task_name, task_level=1)
            )
            db.session.add(sequence)
    db.session.commit()

def sequence_instantiate(seq, event_manager):
    sequence = ADSSequence(id=seq.id,
                           taskName=seq.name,
                           parallelizable=seq.parallelizable,
                           event_manager=event_manager)
    tasks = []
    for task in seq.children:
        if task.task_type == 'task':
            t = ADSTask(id=task.id, taskName=task.name)
            user_code = UserCode(task)
            t.setUserCode(user_code)
            sequence.addTask(t)
            #tasks.append(t)
        else:
            #t = Sequence(taskName=task.name,
            #             parallelizable=task.parallelizable,
            #             server=server)
            #tasks.append(t)
            subsequence = sequence_instantiate(task, event_manager)
            sequence.addTask(subsequence)
            #subtasks = subtasks_instantiate(task, server)
            #tasks.extend(subtasks)
    #return tasks
    return sequence

def get_tasks(seq):
    sequence = {
        'id': seq.id,
        'name': seq.name,
        'description': seq.description,
        'directive': 'RUN',
        'result': results["NOT_STARTED"],
        'children': []
    }
    for task in seq.children:
        if task.task_type == 'task':
            t = {
                'id': task.id,
                'name': task.name,
                'description': task.description,
                'directive': 'RUN',
                'result': results["FINISHED"],
            }
        else:
            t = get_tasks(task)
        sequence["children"].append(t)
    return sequence

@app.route('/commissioning/load-sequences')
def load_sequences():
    sequences = []
    sequences_root = db.session.query(Task).filter((Task.task_type == 'seq')
                                                   & (Task.task_level == 0)).all()
    for seq in sequences_root:
        sequences.append(get_tasks(seq))
    print(sequences)
    return jsonify({
        'sequences': sequences
    })


def execute_sequence(sequence_name):
    server = None
    tasks = []
    seq = db.session.query(Task).filter(Task.name==sequence_name).first()
    tasks.append(sequence)
    subtasks = subtasks_instantiate(seq, server)
    tasks.extend(subtasks)
    for t in tasks:
        if isinstance(t, Sequence):
            continue
        t.userCode.execUserCode()

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
            'beam_time': self.times,
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

    def __repr__(self):
        return self.name

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')
