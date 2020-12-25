import abc

class AbstractTaskImpl(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def exec(self):
        pass

    @abc.abstractmethod
    def execUserCode(self):
        pass

    @abc.abstractmethod
    def execPreUserCode(self):
        pass

    @abc.abstractmethod
    def execPostUserCode(self):
        pass

