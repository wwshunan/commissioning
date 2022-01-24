import abc
from .callable_task import CallableTask

class Sequence(CallableTask):
    @abc.abstractmethod
    def isParallel(self):
        pass

    @abc.abstractmethod
    def addTask(self, task):
        pass

    @abc.abstractmethod
    def cancel(self, orderly):
        pass

    @abc.abstractmethod
    def getTaskList(self):
        pass

    @abc.abstractmethod
    def getFlattenedTaskList(self):
        pass

    @abc.abstractmethod
    def printFlattenedTaskListExecutionResults(self):
        pass

    @abc.abstractmethod
    def printTaskListExecutionResults(self):
        pass

    @abc.abstractmethod
    def getSequenceExecutorService(self):
        pass
