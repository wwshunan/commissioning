from fastapi import APIRouter, Depends, UploadFile, File, Form, WebSocket, HTTPException
from ..dependencies import calc_energy, get_db
from .lattice import load_lattice, set_lattice, set_sync_phases, check_all_magnets
from ..utils import remove_empty_element
from sqlalchemy.orm import Session
from ..crud import log_lattice
import aioredis
import fastapi_plugins
import json

router = APIRouter()


@router.post('/commissioning/energy-compute')
def energy_computation(result: dict = Depends(calc_energy)):
    return result


@router.post('/commissioning/lattice-upload')
async def lattice_upload(section: str = Form(...),
                         lattice_file: UploadFile = File(...),
                         cache: aioredis.Redis = Depends(fastapi_plugins.depends_redis),
                         ) -> str:
    lattice_data = load_lattice(lattice_file.file, section)
    remove_empty_element(lattice_data)
    serialized_lattice_data = json.dumps(lattice_data)
    await cache.set('lattice_data', serialized_lattice_data)
    return dict(code=20000)


@router.post('/commissioning/lattice-setting')
async def lattice_setting(db: Session = Depends(get_db),
                          cache: aioredis.Redis = Depends(fastapi_plugins.depends_redis)):
    lattice_data = await cache.get('lattice_data')
    lattice_data = json.loads(lattice_data)
    set_lattice(lattice_data)
    set_sync_phases(lattice_data)
    log_lattice(db, lattice_data)

    return dict(code=20000)

@router.get("/commissioning/lattice-check")
async def lattice_check(cache: aioredis.Redis = Depends(fastapi_plugins.depends_redis)):
    lattice_data = await cache.get('lattice_data')
    lattice_data = json.loads(lattice_data)
    try:
        return dict(code=20000, diff_magnets=check_all_magnets(lattice_data))
    except TypeError:
        raise HTTPException(status_code=500, detail="PV量无法连接!")

'''
@router.post('/lattice-query')
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


@router.get('/log/start')
def start_time_accumulate():
    interrupt_id = uuid.uuid4().hex
    time_break_id = uuid.uuid4().hex
    redis_client.set(interrupt_id, 'false')
    redis_client.set(time_break_id, 'false')
    redis_client.set('finished', 'false')
    # interrupt_id, time_break_id = rpc.usage_time_service.start()
    cache.set('interrupt', interrupt_id)
    cache.set('time_break', time_break_id)
    with open('timing-id.txt', 'w') as fobj:
        fobj.write('{}\t{}\n'.format(interrupt_id, time_break_id))
    accumulate_time.delay(interrupt_id, time_break_id)
    return jsonify(status='Success')


@router.get('/warning/robot-start')
def start_robot():
    robot_id = uuid.uuid4().hex
    redis_client.set(robot_id, 'false')
    with open('robot-id.txt', 'w') as fobj:
        fobj.write('{}\n'.format(robot_id))
    send_alarm.delay(robot_id)
    return jsonify(status='Success')


@router.get('/warning/robot-stop')
def stop_robot():
    with open('robot-id.txt') as fobj:
        robot_id = fobj.readlines()[0].strip()
    print(robot_id)
    redis_client.set(robot_id, 'true')
    return 'SUCCESS'


@router.get('/warning/cavity_monitor_start')
def start_cavity_monitor():
    cavity_monitor_id = uuid.uuid4().hex
    redis_client.set(cavity_monitor_id, 'false')
    with open('cavity_ready.txt', 'w') as fobj:
        fobj.write('{}\n'.format(cavity_monitor_id))
    send_alarm_cavity.delay(cavity_monitor_id)
    return jsonify(status='Success')


@router.get('/warning/cavity_monitor_stop')
def stop_cavity_monitor():
    with open('cavity_ready.txt') as fobj:
        cavity_monitor_id = fobj.readlines()[0].strip()
    print(cavity_monitor_id)
    redis_client.set(cavity_monitor_id, 'true')
    return 'SUCCESS'


@router.get('/log/stop')
def stop_time_accumulate():
    with open('timing-id.txt') as fobj:
        time_break_id = fobj.readlines()[0].split()[1]
    redis_client.set(time_break_id, 'true')
    return 'SUCCESS'


@router.get('/log/interrupt')
def interrupt_timing():
    with open('timing-id.txt') as fobj:
        interrupt_id = fobj.readlines()[0].split()[0]

    redis_client.set(interrupt_id, 'true')
    while redis_client.get(interrupt_id) == b'true':
        time.sleep(0.1)
    usage_time = redis_client.get('usage_time')

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


@router.post('/log/time-query')
def time_query():
    post_data = request.get_json()
    start_date = datetime.strptime(post_data['startDate'], "%Y-%m-%dT%H:%M:%S.%fZ")
    to_date = datetime.strptime(post_data['toDate'], "%Y-%m-%dT%H:%M:%S.%fZ")
    query_condition = Timing.query.filter(
        Timing.timestamp >= start_date).filter(Timing.timestamp <= to_date)

    timing_info = []
    timings = query_condition.all()
    # timing_data = [datetime.strptime(t.timestamp, '')]
    for t in timings:
        timing_info.append(t.to_json())
    return jsonify({
        'usage_time': timing_info
    })


@router.post('/log/snapshot')
def snapshot():
    loop_num = 6
    data = request.get_json()
    selected_sections = data['selected_sections']
    if redis_client.exists('selected_sections'):
        redis_client.delete('selected_sections')
    redis_client.rpush('selected_sections', *selected_sections)
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
        'routerms': BPM
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


@router.get('/log/snapshot-checkout')
def snapshot_checkout():
    selected_sections = redis_client.lrange('selected_sections', 0, 10)
    selected_sections = [x.decode('utf-8') for x in selected_sections]
    diffs = checkout_sections(selected_sections)
    return jsonify({
        'diffs': diffs
    })


@router.post('/commissioning/task-stop')
def task_stop():
    stop_event = PrioritizedItem(0, 'stop')
    event_manager.send_task(stop_event)
    return jsonify({
        'status': 'OK'
    })


@router.post('/commissioning/task-step')
def task_step():
    task_id = request.get_json()['id']
    seq = redis_client.hgetall('selected_sequence')
    sequence = select_sequence(seq)
    tasks = sequence.getFlattenedTaskList()
    manager = sequence.event_manager
    i = 0
    for t in tasks:
        if t.id == task_id:
            task = t
            if i < len(tasks) - 1:
                next_task_id = tasks[i + 1].id
            else:
                next_task_id = tasks[i].id
            break
        i += 1
    task_item = PrioritizedItem(1, task.userCode.execUserCode)
    manager.send_task(task_item)

    from .flask_app_mod import socket_io
    socket_io.emit('next_task', {
        'next_task_id': next_task_id
    })
    return jsonify({
        'stauts': 'OK'
    })


@router.post('/commissioning/sequence-init')
def sequence_init():
    global sequence_to_execute
    # EVENT_STARTUP = 'Event_Startup'
    # EVENT_FINISHED = 'Event_Finished'
    # event_manager.add_event_worker(EVENT_STARTUP, )
    sequence = request.get_json()
    redis_client.hmset('selected_sequence', sequence)
    return jsonify({
        'status': 'OK'
    })


@router.post('/commissioning/sequence-execute')
def sequence_execute():
    # sequence = sequence_instantiate(seq, executor)
    seq = redis_client.hgetall('selected_sequence')
    sequence = select_sequence(seq)
    sequence.execUserCode()
    return jsonify({
        "status": "OK"
    })


@router.get('/commissioning/load-sequences')
def load_sequences():
    sequences = []
    sequences_root = db.session.query(Task).filter((Task.task_type == 'seq')
                                                   & (Task.task_level == 0)).all()
    for seq in sequences_root:
        sequences.append(get_tasks(seq))
    return jsonify({
        'sequences': sequences
    })
'''

