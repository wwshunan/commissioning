from .callable_task import CallableTask
from .sequence import Sequence
from .task_parameter import TaskParameter
from .abstract_task_impl import AbstractTaskImpl
from datetime import datetime
import threading
from .priority_item import PrioritizedItem

class ADSTask(AbstractTaskImpl, CallableTask):
    def __init__(self, taskName='', description='', sequence=None,
                 runnable_code=None, reference=None, parameter=None,
                 repititionNumber=1, repititionCount=0, sequenceName='',
                 skippable=False, interactive=False, taskBreakPoint=False,
                 skipTaskState=False, skippableState=False, deviceName='',
                 id=1):
        self.id = id
        self.parameter = parameter
        self.deviceName = deviceName
        self.sequenceName = sequenceName
        self.sequence = sequence
        self.reference = reference
        self.taskName = taskName
        self.repititionNumber = repititionNumber
        self.repititionCount = repititionCount
        self.description = description
        self.skippable = skippable
        self.interactive = interactive
        self.userCode = None
        self.runnable_code = runnable_code
        self.taskBreakPoint = taskBreakPoint
        self.skipTaskState = skipTaskState
        self.skippableState = skippableState

    def getDeviceName(self):
        return self.deviceName

    def getParameter(self):
        return self.parameter

    def setParameter(self, taskParameter):
        self.parameter = taskParameter
        return this

    def getSequenceName(self):
        return self.sequenceName

    def getSequence(self):
        return self.sequence

    def setSequence(self, sequence):
        self.sequence = sequence
        return this

    def getReferences(self):
        return self.reference

    def addReference(self, infoReference):
        self.reference = infoReference
        return this

    def getTaskName(self):
        return self.taskName

    def setTaskName(self, name):
        self.taskName = name
        return this

    def getUniqueTaskID(self):
        pass

    def getTaskDescription(self):
        return self.description

    def setTaskDescription(self, description):
        self.description = description
        return this

    def getCallingSequence(self):
        return self.sequence

    def getSequenceLevel(self):
        pass

    def getSequenceTestId(self):
        pass

    def getSequenceTestStart(self):
        pass

    def getTaskStartTime(self):
        return datetime.now()

    def getTaskEndTime(self):
        return datetime.now()

    def getTaskRepetitionNumber(self):
        return self.repititionNumber

    def setTaskRepitionNumber(self, value):
        self.repititionNumber = value
        return this

    def getTaskRepititionCount(self):
        return self.repititionCount

    def isTaskInteractive(self):
        return self.interactive

    def isSkippable(self):
        return self.skippable

    def getUserName(self):
        pass

    def setUserCode(self, userCode):
        self.userCode = userCode

    def setPreUserCode(self, userCode):
        pass

    def setPostUserCode(self, userCode):
        pass

    def setErrorRecoveryUserCode(self, userCode):
        pass

    def getTaskResult(self):
        pass

    def setTaskBreakPoint(self, state):
        self.taskBreakPoint = state

    def isTaskBreakPointSet(self):
        return self.taskBreakPoint

    def setSkipTaskState(self, state):
        self.skipTaskState = state

    def isTaskSkipStateSet(self):
        return self.skipTaskState

    def setSkippableState(self, state):
        self.skippableState = state

    def addUpdateListener(self, listener):
        self.listener = listener

    def removeUpdateListener(self, listener):
        self.listener = None

    def reset(self):
        self.taskBreakPoint = False
        self.skipTaskState = False
        self.skippableState = False

    def getPendingUserCallback(self):
        pass

    def replyToPendingUserCallback(self, reply):
        pass

    def exec(self):
        self.execPreUserCode()
        self.execUserCode()
        self.execPostUserCode()

    def execPreUserCode(self):
        pass

    def execUserCode(self):
        return self.runnable_code()

    def execPostUserCode(self):
        pass

    def __repr__(self):
        return self.taskName

class ADSSequence(AbstractTaskImpl, Sequence):
    def __init__(self, parameter=None, deviceName='', sequenceName='',
                 sequence=None, reference=None, taskName='',
                 repititionNumber=1, repititionCount=0, description='',
                 skippable=False, interactive=False, taskBreakPoint=False,
                 skipTaskState=False, skippableState=False, id=1,
                 parallelizable=False, event_manager=None):
        self.id = id
        self.parameter = parameter
        self.deviceName = deviceName
        self.sequenceName = sequenceName
        self.sequence = sequence
        self.reference = reference
        self.taskName = taskName
        self.repititionNumber = repititionNumber
        self.repititionCount = repititionCount
        self.description = description
        self.skippable = skippable
        self.interactive = interactive
        self.userCode = None
        self.taskBreakPoint = taskBreakPoint
        self.skipTaskState = skipTaskState
        self.skippableState = skippableState
        self.parallelizable=parallelizable
        #self.executor=executor
        self.event_manager = event_manager
        self.tasks = []

    def getDeviceName(self):
        return self.deviceName

    def getParameter(self):
        return self.parameter

    def setParameter(self, taskParameter):
        self.parameter = taskParameter
        return this

    def getSequenceName(self):
        return self.sequenceName

    def getSequence(self):
        return self.sequence

    def setSequence(self, sequence):
        self.sequence = sequence
        return this

    def getReferences(self):
        return self.reference

    def addReference(self, infoReference):
        self.reference = infoReference
        return this

    def getTaskName(self):
        return self.taskName

    def setTaskName(self, name):
        self.taskName = name
        return this

    def getUniqueTaskID(self):
        pass

    def getTaskDescription(self):
        return self.description

    def setTaskDescription(self, description):
        self.description = description
        return this

    def getCallingSequence(self):
        return self.sequence

    def getSequenceLevel(self):
        pass

    def getSequenceTestId(self):
        pass

    def getSequenceTestStart(self):
        pass

    def getTaskStartTime(self):
        return datetime.now()

    def getTaskEndTime(self):
        return datetime.now()

    def getTaskRepetitionNumber(self):
        return self.repititionNumber

    def setTaskRepitionNumber(self, value):
        self.repititionNumber = value
        return this

    def getTaskRepititionCount(self):
        return self.repititionCount

    def isTaskInteractive(self):
        return self.interactive

    def isSkippable(self):
        return self.skippable

    def getUserName(self):
        pass

    def setUserCode(self, userCode):
        self.userCode = userCode

    def setPreUserCode(self, userCode):
        pass

    def setPostUserCode(self, userCode):
        pass

    def setErrorRecoveryUserCode(self, userCode):
        pass

    def getTaskResult(self):
        pass

    def setTaskBreakPoint(self, state):
        self.taskBreakPoint = state

    def isTaskBreakPointSet(self):
        return self.taskBreakPoint

    def setSkipTaskState(self, state):
        self.skipTaskState = state

    def isTaskSkipStateSet(self):
        return self.skipTaskState

    def setSkippableState(self, state):
        self.skippableState = state

    def addUpdateListener(self, listener):
        self.listener = listener

    def removeUpdateListener(self, listener):
        self.listener = None

    def reset(self):
        self.taskBreakPoint = False
        self.skipTaskState = False
        self.skippableState = False

    def getPendingUserCallback(self):
        pass

    def replyToPendingUserCallback(self, reply):
        pass

    def exec(self):
        self.execPreUserCode()
        self.execUserCode()
        self.execPostUserCode()

    def execPreUserCode(self):
        pass

    def execUserCode(self):
        #executor = self.executor
        event_manager = self.event_manager
        priority = 1
        for task in self.getFlattenedTaskList():
            task_item = PrioritizedItem(priority, task.userCode.execUserCode)
            event_manager.send_task(task_item)
            priority += 1
            #executor.submit(task.userCode.execUserCode)

    def execPostUserCode(self):
        pass

    def isParallel(self):
        return self.parallelizable

    def addTask(self, task):
        self.tasks.append(task)
        return task

    def cancel(self, orderly):
        if self.executorService:
            self.executorService.cancel()

    def getTaskList(self):
        return self.tasks

    def getFlattenedTaskList(self):
        flattenedTaskList = []
        for task in self.tasks:
            if isinstance(task, Sequence):
                flattenedTaskList.extend(task.getFlattenedTaskList())
            else:
                flattenedTaskList.append(task)
        return flattenedTaskList

    def printFlattenedTaskListExecutionResults(self):
        results = []
        flattenedTaskList = self.getFlattenedTaskList()
        for task in flattenedTaskList:
            results.append(task.getResult())
        return results

    def printTaskListExecutionResults(self):
        results = []
        for task in self.tasks:
            results.append(task.getResult())
        return results

    def getSequenceExecutorService(self):
        return self.executorService

    def __repr__(self):
        return self.taskName
