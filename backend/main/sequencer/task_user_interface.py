import abc

class TaskUserInterface(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def execUserCode(self, task):
        pass