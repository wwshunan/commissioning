from .sequence.task_impl import ADSSequence, ADSTask
from .sequence.task_user_interface import TaskUserInterface
import importlib

class UserCode(TaskUserInterface):
    def __init__(self, task):
        self.module = 'backend.sequencer.user_codes.tasks'
        self.task = task

    def execUserCode(self):
        mod = importlib.import_module(self.module)
        user_code = getattr(mod, self.task.user_code)
        try:
            user_code()
            result = {
                'key': 'OK',
                'detail': 'FINISHED'
            }
        except Exception as e:
            result = {
                'key': 'FAILURE',
                'detail': e.error_info
            }
        finally:
            return result

class TaskExecutor(object):
    def __init__(self, executor) -> None:
        self.sequence = None
        self.executor = executor
    
    def initialize_sequence(self, seq):
        self.sequence = self._initialize_sequence(seq)

    def _initialize_sequence(self, seq):
        sequence = ADSSequence(
            id=seq.id, taskName=seq.name, parallelizable=seq.parallelizable)
        for task in seq.children:
            if task.task_type == 'task':
                t = ADSTask(id=task.id, taskName=task.name)
                user_code = UserCode(task)
                t.setUserCode(user_code)
                sequence.addTask(t)
            else:
                subsequence = self._initialize_sequence(task)
                sequence.addTask(subsequence)
        return sequence

    def execute_sequence(self):
        return self.sequence.execUserCode(self.executor)

    def execute_task(self, task_id):
        tasks = self.sequence.getFlattenedTaskList()
        task = next(filter(lambda x: x.id==task_id, tasks), None)
        #for i, t in enumerate(tasks):
        #    if t.id == task_id:
        #        task = t
        #        next_task_id = tasks[i+1].id if i < len(tasks) - 1 else tasks[i].id
        #        break
        return task.execUserCode(self.executor)
