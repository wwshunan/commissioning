#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 20-7-24 下午23:32
# @Author  : pang
# @Software: PyCharm
import os
import json
import pickle
import time
import struct
import threading
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

_HEADER_FMT = "!8slQ16s16slQ"
_HEADER_LENGTH = struct.calcsize(_HEADER_FMT)


MSG_HEAD = b'sbyukuai'


def spawn_id():
    if not hasattr(spawn_id, 'lock'):
        spawn_id.lock = threading.Lock()
    if not hasattr(spawn_id, 'index'):
        spawn_id.index = 0
    with spawn_id.lock:
        spawn_id.index += 1
        return spawn_id.index


class Singleton(object):
    def __init__(self, cls):
        self.__instance = None
        self.__cls = cls
        self._lock = threading.Lock()

    def __call__(self, *args, **kwargs):
        self._lock.acquire()
        if self.__instance is None:
            self.__instance = self.__cls(*args, **kwargs)
        self._lock.release()
        return self.__instance


class MsgFlag:
    URGENT = 0X00000001
    NORMAL = 0X00000002
    NEED_ACK = 0X00000004
    ACK = 0X00000008


class FunctionCode(object):
    AUTH = 10
    TEST = 1001
    FOO1 = 1002


class Message(object):
    """
    _ORDER = ['head', 'flag', 'len', 'from', 'to', 'fc', 'req_id', 'body']

    """
    
    def __init__(self):
        self._msg_finish = False        # True 才可以访问属性
        self._buffer = b''
        self._header = False
        self._head = MSG_HEAD
        self._flag = MsgFlag.NORMAL
        self._body_length = 0
        self._from_addr = None
        self._to_addr = None
        self._function_code = None
        self._req_id = None
        self._body = None
        self.protocol = None

    def __del__(self):
        self.protocol = None

    @property
    def flag(self):
        return self._flag

    def add_flag(self, flag):
        self._flag |= flag

    def remove_flag(self, flag):
        self._flag ^= flag

    @property
    def fc(self):
        return self._function_code

    @property
    def head(self):
        return self._head

    @property
    def from_addr(self):
        return self._from_addr

    @property
    def to_addr(self):
        return self._to_addr

    @property
    def req_id(self):
        return self._req_id
        
    def __repr__(self):
        return f"fc:{self._function_code}, flag:{self._flag} req_id:{self._req_id}, body:{self.body}"
    
    __str__ = __repr__
    
    @classmethod
    def spawn_post_msg(cls, fc=0, data=None, req_id=None, flag=MsgFlag.NORMAL, from_addr=None, to_addr=None):
        instance = cls()
        instance._function_code = fc
        instance._body = data
        instance._req_id = req_id or spawn_id()
        instance._flag = flag or MsgFlag.NORMAL
        instance._from_addr = from_addr or ''
        instance._to_addr = to_addr or ''
        return instance
    
    @classmethod
    def spawn_resp_msg(cls):
        return cls()

    @property
    def buffer(self):
        return memoryview(self._buffer)
    
    @property
    def body(self):
        return self._body
    
    @staticmethod
    def encode(data):
        """
        body序列化
        :param data:
        :return:
        """
        return pickle.dumps(data)
    
    @property
    def dump_data(self):
        body = self.encode(self._body)
        from_address = self.encode(self._from_addr)
        to_address = self.encode(self._to_addr)
        fmt = "%s%ds" % (_HEADER_FMT, len(body))
        return struct.pack(
            fmt, self._head, self._flag, len(body),
            from_address, to_address, self._function_code,
            self._req_id, body)
    
    @staticmethod
    def decode(data):
        """
        body反序列化
        :param data:
        :return:
        """
        return pickle.loads(data)
    
    def push_data(self, junk: bytes):
        """
        push data into the msg. Return pushed length.
        Return -1 if we should shutdown the socket channel.
        :param junk:
        :return: 返回成值 小于 junk的长度，则说明这个包已经完成了， 等于可能完成
        """
        if self._msg_finish:
            logger.warning('The Message has already been pushed enough data')
            return 0
        if len(junk) == 0:
            logger.warning('You just pushed into the msg with a zero-length data')
            return 0
        junk_length = len(junk)
        buffer_length = len(self._buffer)
        if buffer_length + junk_length < _HEADER_LENGTH:
            self._buffer += junk
            return junk_length
        index = 0
        msg_length = buffer_length + junk_length
        if self._header is False and msg_length >= _HEADER_LENGTH:
            # 头 已经收完了
            index = _HEADER_LENGTH - buffer_length
            self._buffer += junk[:index]
            _header = struct.unpack(_HEADER_FMT, self._buffer)
            # ['head', 'flag', 'len', 'from', 'to', 'fc', 'req_id', 'body']
            self._head = _header[0]
            self._flag = _header[1]
            self._body_length = _header[2]
            self._from_addr = _header[3]
            self._to_addr = _header[4]
            self._function_code = _header[5]
            self._req_id = _header[6]
            self._header = True
            # self._body_length = dict(zip(_ORDER, self._header))['len']
        if self._header :
            if msg_length >= _HEADER_LENGTH + self._body_length:
                # 头 已经收完了, 开始接收body数据
                diff = (_HEADER_LENGTH + self._body_length) - len(self._buffer)
                self._buffer += junk[index:index+diff]
                index += diff
                self._body = self._buffer[_HEADER_LENGTH:]
                self._body = self.decode(self._body)
                self._msg_finish = True
                self._buffer = None     # 清空免得占用双份内存
                # 完成
            else:
                self._buffer += junk[index:]
                index += len(junk[index:])
        return index
    
    def is_finished(self):
        return self._msg_finish


def test_message():
    x = b'PL\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x06192.168.1.1\x00\x00\x00\x00\x00192.168.1.2\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x01'
    msg = Message()
    print(msg.push_data(x[:10]))
    print(msg.push_data(x[10:]))
    print(msg.push_data(b'123456'))
    
    x = b'PL\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x06192.168.1.1\x00\x00\x00\x00\x00192.168.1.2\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x01\x55'
    msg = Message()
    print(msg.push_data(x[:10]))
    print(msg.push_data(x[10:20]))
    print(msg.push_data(x[20:]))
    print(msg.push_data(b'23456716354165'))


class Protocol(asyncio.Protocol):
    executor = ThreadPoolExecutor(4)
    
    def __init__(self, message_handler=None, loop=None, timeout=10):
        self.loop = loop or asyncio.get_event_loop()
        self.message_handler = message_handler or BaseMessageHandler
        self.message_handler = self.message_handler()
        self._wait_reply_message_map = {}
        self.transport = None
        self.message = None
        self.recv_msg_q = asyncio.Queue()
        self.post_msg_q = asyncio.PriorityQueue()
        self._connected = True
        self._msg_index = 0
        self.timeout = timeout
        asyncio.run_coroutine_threadsafe(self._write_worker(), self.loop)
        asyncio.run_coroutine_threadsafe(self._read_worker(), self.loop)

    async def join(self):
        await self.post_msg_q.join()
        await self.recv_msg_q.join()

    def close(self):
        if self.transport:
            self.transport.close()

    def connection_made(self, transport):
        self.transport = transport
        self.message_handler.set_protocol(self)
        logger.debug('a connection is made.')

    def data_received(self, data):
        if len(data) == 0:
            return
        if self.message is None:
            self.message = Message.spawn_resp_msg()
        data_index = 0
        while True:
            data_index += self.message.push_data(data[data_index:])
            if self.message.is_finished():
                self.message.protocol = self
                self.recv_msg_q.put_nowait(self.message)
                self.message = Message.spawn_resp_msg()
            if len(data) == data_index:
                break
    
    def connection_lost(self, exc):
        logger.debug('The server closed the connection')
        self._connected = False

    def write(self, message):
        urgency = 1
        if (message.flag & MsgFlag.URGENT) == MsgFlag.URGENT:
            # 如果紧急就发前面
            urgency = 0
        self.post_msg_q.put_nowait((urgency, self._msg_index, message))
        self._msg_index += 1
        if (message.flag & MsgFlag.NEED_ACK) == MsgFlag.NEED_ACK:
            f = self.loop.create_future()
            self._wait_reply_message_map[message.req_id] = f
            return f
        else:
            return None

    async def _write_worker(self):
        logger.debug('begin write worker.')
        while self._connected:
            _, index, message = await self.post_msg_q.get()
            self.post_msg_q.task_done()
            self.transport.write(message.dump_data)
            logger.debug('Write message. %s' % str(message))

    def raw_write(self, message):
        self.transport.write(message.dump_data)
        logger.debug('Write message. %s' % str(message))

    def _wraps_reply_message(self, message):
        post_message = self.message_handler.reply_message(message=message)
        if not isinstance(post_message, Message):
            raise TypeError("type must be Message.")
        if message.req_id != post_message.req_id:
            raise ValueError('message and reply message have different req_id.')
        post_message.remove_flag(MsgFlag.NEED_ACK)
        post_message.add_flag(MsgFlag.ACK)
        self.write(post_message)

    async def _read_worker(self):
        logger.debug('begin read worker.')
        while self._connected:
            message = await self.recv_msg_q.get()
            logger.debug('Read message. %s.' % str(message))
            self.recv_msg_q.task_done()
            if message.flag & MsgFlag.NEED_ACK == MsgFlag.NEED_ACK:
                task = self.call_soon(self._wraps_reply_message, message)
                # self.loop.create_task(task)
            if message.flag & MsgFlag.ACK == MsgFlag.ACK:
                if message.req_id in self._wait_reply_message_map:
                    self._wait_reply_message_map[message.req_id].set_result(message)
                    del self._wait_reply_message_map[message.req_id]
                else:
                    logger.warning("error reply message. message:%s" % message)
            task = self.call_soon(self.message_handler.on_message, message)
            # self.loop.create_task(task)

    def call_soon(self, func, *args):
        return self.loop.run_in_executor(self.executor, func, *args)
        # return self.loop.call_soon(func, *args)
    
    def call_later(self, delay, callback, *args):
        return self.loop.call_later(delay, callback, *args)


class KeepaliveProtocol(Protocol):
    pass


class BaseMessageHandler(object):

    def __init__(self):
        self.protocol = None

    def set_protocol(self, protocol):
        self.protocol = protocol

    def on_message(self, message: Message):
        """
        所有消息
        :param message:
        :return:
        """
        pass

    def reply_message(self, message):
        """
        收到的需要回复的消息
        :param message: 回复的消息
        :return:
        """
        post_message = Message.spawn_post_msg(
            fc=message.fc,
            data=MsgFlag.NEED_ACK,
            req_id=message.req_id,
            flag=message.flag,
            from_addr=message.to_addr,
            to_addr=message.from_addr,
        )
        return post_message


class Switch(object):
    _map = {}

    def __init__(self, fc):
        self._fc = fc

    def __call__(self, function, *args, **kwargs):
        if self._fc in self._map:
            raise ValueError('This fc already exists. %s' % self._fc)
        self._map[self._fc] = function
        return function

    @staticmethod
    def case(fc):
        func = Switch._map.get(fc)
        if func is not None:
            return func
        else:
            raise ValueError('There is no such fc. %s' % fc)


def get_logger(log_path='app.log', log_level=logging.DEBUG):
    log_format = '[%(levelname)-7s][%(asctime)s][%(filename)s][line:%(lineno)s]: %(message)s'
    result = logging.getLogger()
    dir_name = os.path.dirname(log_path)
    if dir_name and not os.path.isdir(dir_name):
        os.makedirs(dir_name)
    result.handlers = []
    logging.basicConfig(level=log_level,
                        format=log_format,
                        filename=log_path,
                        filemode='a')
    console = logging.StreamHandler()
    console.setLevel(log_level)
    formatter = logging.Formatter(log_format)
    console.setFormatter(formatter)
    result.addHandler(console)
    return result

