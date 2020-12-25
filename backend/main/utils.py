from werkzeug.utils import secure_filename
from .sequencer.task_impl import ADSTask, ADSSequence
from .sequencer.task_state import TaskState
from .event_manager import EventManager
from .factory import db


event_manager = EventManager()
event_manager.start()

sequence_to_execute = None


def remove_dict_null(data):
    copied_keys = tuple(data.keys())
    for key in copied_keys:
        if isinstance(data[key], dict) and data[key]:
            remove_dict_null(data[key])
        if not data[key]:
            data.pop(key)

def save_timing(timing_data):
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

def remove_dict_null(data):
    copied_keys = tuple(data.keys())
    for key in copied_keys:
        if isinstance(data[key], dict) and data[key]:
            remove_dict_null(data[key])
        if not data[key]:
            data.pop(key)


