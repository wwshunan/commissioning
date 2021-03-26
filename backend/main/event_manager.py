from queue import PriorityQueue, Empty
from threading import *
from flask_socketio import SocketIO
import time
from concurrent.futures import ThreadPoolExecutor


class EventManager(object):

    def __init__(self, worker_num=1):
        """初始化事件管理器"""
        # 事件对象列表
        self.__taskQueue = PriorityQueue()
        # 事件管理器开关
        self.__active = False
        # 事件处理线程
        self.__thread = Thread(target=self.__run)
        # 这里的__handlers是一个字典，用来保存对应的事件的响应函数
        # 其中每个键对应的值是一个列表，列表中保存了对该事件监听的响应函数，一对多
        self.__handlers = {}
        self.worker_num = worker_num
        self.executor = ThreadPoolExecutor(max_workers=worker_num)

    def set_worker_num(self, worker_num):
        self.executor = ThreadPoolExecutor(max_workers=worker_num)

    def __run(self):
        """引擎运行"""
        while self.__active == True:
            try:
                # 获取事件的阻塞时间设为1秒
                task = self.__taskQueue.get(block=True, timeout=1)
                if task.item == 'stop':
                    with self.__taskQueue.mutex:
                        self.__taskQueue.queue.clear()
                        continue
                if self.worker_num == 1:
                    result = self.serial_task(task)
                    #result = self.__task_process(task)
                else:
                    #self.__task_process(task)
                    self.parallevel_task(task)
            except Empty:
                pass

    def parallevel_task(self, task):
        self.executor.submit(task.item)

    def serial_task(self, task):
        future = self.executor.submit(task.item)
        result = future.result()
        return result

    def start(self):
        """启动"""
        # 将事件管理器设为启动
        self.__active = True
        # 启动事件处理线程
        self.__thread.start()

    def stop(self):
        """停止"""
        # 将事件管理器设为停止
        self.__active = False
        # 等待事件处理线程退出
        self.__thread.join()

    def send_task(self, task):
        """发送事件，向事件队列中存入事件"""
        self.__taskQueue.put(task)

event_manager = EventManager()
event_manager.start()

if __name__ == '__main__':
    pass
