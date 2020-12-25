from .factory import db
from .models import Task
from .sequencer.task_impl import ADSTask, ADSSequence
from .sequencer.task_state import TaskState
from .sequencer.task_user_interface import TaskUserInterface
from .event_manager import event_manager
import importlib

task_status = {
    'NOT_STARTED': "<span>NOT_STARTED</span>",
    'FINISHED': "<span style='color: green; '>FINISHED</span>",
    'FINISHED_FAULTY': "<span style='color: red; '>FINISHED_FAULTY</span>",
    'SKIPPED': "<span style='color: yellow; '>SKIPPED</span>",
}

def select_sequence(sequence):
    seq = db.session.query(Task).filter(Task.id == sequence[b'id'].decode('utf-8')).first()
    worker_num = 1
    if seq.parallelizable:
        worker_num = 5

    event_manager.set_worker_num = worker_num
    # executor = ThreadPoolExecutor(max_workers=worker_num)
    sequence = sequence_instantiate(seq, event_manager)
    sequence_to_execute = sequence
    return sequence_to_execute

def get_tasks(seq):
    sequence = {
        'id': seq.id,
        'name': seq.name,
        'description': seq.description,
        'directive': 'RUN',
        'result': task_status["NOT_STARTED"],
        'children': []
    }
    for task in seq.children:
        if task.task_type == 'task':
            t = {
                'id': task.id,
                'name': task.name,
                'description': task.description,
                'directive': 'RUN',
                'result': task_status["FINISHED"],
            }
        else:
            t = get_tasks(task)
        sequence["children"].append(t)
    return sequence

class UserCode(TaskUserInterface):
    def __init__(self, task):
        self.module = 'backend.main.sequencer.user_codes.tasks'
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
            from backend.main.flask_app_mod import socket_io 
            socket_io.emit('finished', {
                'status': status,
                'id': self.task.id,
                'name': self.task.name
            })
            return status

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

