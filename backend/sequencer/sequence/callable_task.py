from .task_info import TaskInfo
import abc

class CallableTask(TaskInfo):
    @abc.abstractmethod
    def getTaskResult(self):
        pass

    @abc.abstractmethod
    def setTaskBreakPoint(self, state):
        pass

    @abc.abstractmethod
    def isTaskBreakPointSet(self):
        pass

    @abc.abstractmethod
    def setSkipTaskState(self, state):
        pass

    @abc.abstractmethod
    def isTaskSkipStateSet(self):
        pass

    @abc.abstractmethod
    def setSkippableState(self, state):
        pass

    @abc.abstractmethod
    def addUpdateListener(self, listener):
        pass

    @abc.abstractmethod
    def removeUpdateListener(self, listener):
        pass

    @abc.abstractmethod
    def reset(self):
        pass

    @abc.abstractmethod
    def getPendingUserCallback(self):
        pass

    @abc.abstractmethod
    def replyToPendingUserCallback(self, reply):
        pass