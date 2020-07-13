from werkzeug.utils import secure_filename
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from lattice import load_lattice, generate_info, set_lattice, set_sync_phases
from snapshot_log import get_pv_values, checkout
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy, declarative_base
import os
from datetime import datetime, timedelta
from collections import OrderedDict
from flask_nameko import FlaskPooledClusterRpcProxy
from urllib.parse import unquote
import numpy as np
import time

app = Flask(__name__)

config = {
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "simple", # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 0,
    "SQLALCHEMY_DATABASE_URI": 'sqlite:///lattice.db',
    "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    'JSON_SORT_KEYS': False,
    'NAMEKO_AMQP_URI': 'pyamqp://guest:guest@localhost'
}
app.config.from_mapping(config)
cache = Cache(app)
db = SQLAlchemy(app)
rpc = FlaskPooledClusterRpcProxy(app)

Base = declarative_base()

CORS(app, resources=r'/*')

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
    #f.save(secure_filename(unquote(f.filename)))
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

@app.route('/log/start', methods=['POST'])
def start_time_accumulate():
    time_break_id = rpc.usage_time_service.start()
    cache.set('time_break_id', time_break_id)
    rpc.usage_time_service.accumulate_time.call_async(time_break_id)
    return jsonify(status='Success')

@app.route('/log/stop', methods=["GET"])
def stop_time_accumulate():
    time_break_id = cache.get('time_break_id')
    usage_time = rpc.usage_time_service.stop(time_break_id)
    usage_time = float(usage_time) / 3600
    return jsonify({'usage_time': round(usage_time, 3)})

@app.route('/log/snapshot', methods=['POST'])
def snapshot():
    loop_num = 6
    data = request.get_json()
    selected_sections = data['selected_sections']
    cache.set('selected_sections', selected_sections)
    snapshots = {}
    for i in range(loop_num):
        pv_values = get_pv_values(selected_sections)
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')



