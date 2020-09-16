#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 20-7-24 下午23:32
# @Author  : pang
# @Software: PyCharm

import time
import asyncio
import logging
from common import Message, get_logger, Protocol, MsgFlag
from common import FunctionCode as FC


logger = logging.getLogger(__name__)


class EchoClientProtocol(Protocol):
    
    async def auth(self, user, password):
        s = time.time()
        post_message = Message.spawn_post_msg(FC.AUTH, {'user': user, 'password': password})
        post_message.add_flag(MsgFlag.NEED_ACK)
        recv_message = await self.write(post_message)
        return time.time() - s
    
    def foo(self):
        pass
    
    def on_foo(self):
        pass
    

async def main(loop):
    # Get a reference to the event loop as we plan to use
    # low-level APIs.

    client = EchoClientProtocol(loop=loop)
    transport, protocol = await loop.create_connection(lambda: client, '127.0.0.1', 8888)
    s = time.time()
    tasks = []
    for i in range(10000):
        tasks.append(client.auth('admin', i))
    resp = await asyncio.gather(*tasks)
    print(f"count:{len(resp)}, avg:{sum(resp)/len(resp):.2f}, max:{max(resp):.2f}, min:{min(resp):.2f}")
    await client.join()


def close_after_later(loop):
    loop.stop()


if __name__ == '__main__':
    get_logger('client.log')
    _loop = asyncio.get_event_loop()
    _loop.run_until_complete(main(_loop))
    _loop.call_later(5, close_after_later, _loop)
    _loop.run_forever()

