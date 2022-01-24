import abc

class TaskInfo(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def getDeviceName(self):
        pass

    @abc.abstractmethod
    def getParameter(self):
        pass

    @abc.abstractmethod
    def setParameter(self, taskParameter):
        pass

    @abc.abstractmethod
    def getSequenceName(self):
        pass

    @abc.abstractmethod
    def getSequence(self):
        pass

    @abc.abstractmethod
    def setSequence(self, sequence):
        pass

    @abc.abstractmethod
    def getReferences(self):
        pass

    @abc.abstractmethod
    def addReference(self, infoReference):
        pass

    @abc.abstractmethod
    def getTaskName(self):
        pass

    @abc.abstractmethod
    def setTaskName(self, name):
        pass

    @abc.abstractmethod
    def getUniqueTaskID(self):
        pass

    @abc.abstractmethod
    def getTaskDescription(self):
        pass

    @abc.abstractmethod
    def setTaskDescription(self, description):
        pass

    @abc.abstractmethod
    def getCallingSequence(self):
        pass

    @abc.abstractmethod
    def getSequenceLevel(self):
        pass

    @abc.abstractmethod
    def getSequenceTestId(self):
        pass

    @abc.abstractmethod
    def getSequenceTestStart(self):
        pass

    @abc.abstractmethod
    def getTaskStartTime(self):
        pass

    @abc.abstractmethod
    def getTaskEndTime(self):
        pass

    @abc.abstractmethod
    def getTaskRepetitionNumber(self):
        pass

    @abc.abstractmethod
    def setTaskRepitionNumber(self, value):
        pass

    @abc.abstractmethod
    def getTaskRepititionCount(self):
        pass

    @abc.abstractmethod
    def isTaskInteractive(self):
        pass

    @abc.abstractmethod
    def isSkippable(self):
        pass

    @abc.abstractmethod
    def getUserName(self):
        pass

    @abc.abstractmethod
    def setUserCode(self, userCode):
        pass

    @abc.abstractmethod
    def setPreUserCode(self, userCode):
        pass

    @abc.abstractmethod
    def setPostUserCode(self, userCode):
        pass

    @abc.abstractmethod
    def setErrorRecoveryUserCode(self, userCode):
        pass

    @abc.abstractmethod
    def __repr__(self):
        pass
