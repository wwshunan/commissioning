#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 20-7-24 下午23:32
# @Author  : pang
# @Software: PyCharm

import asyncio
from common import Protocol, Message, get_logger, BaseMessageHandler, MsgFlag


class EchoServerProtocol(Protocol):

    pass


class MessageHandler(BaseMessageHandler):

    def reply_message(self, message: Message):
        post_message = Message.spawn_post_msg(
            fc=message.fc,
            data="密码正确",
            req_id=message.req_id,
            flag=message.flag,
            from_addr=message.to_addr,
            to_addr=message.from_addr,
        )
        return post_message


async def main():
    # Get a reference to the event loop as we plan to use
    # low-level APIs.
    loop = asyncio.get_running_loop()
    server = await loop.create_server(
        lambda: EchoServerProtocol(MessageHandler),
        '127.0.0.1', 8888)

    async with server:
        await server.serve_forever()


get_logger('server.log')
asyncio.run(main())