import asyncio
import functools
import os
import subprocess
import sys
import time

import pytest

import async_patterns.protocol
import modconf.remote

@pytest.fixture
def server():
    p = subprocess.Popen((sys.executable, 'bin/ws_controller', 'runserver', 'ws_controller.tests.conf.simple', '-d'))
    time.sleep(3)
    yield
    p.kill()

class TestConfig:
    def test(self, server):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.atest(loop))

    async def atest(self, loop):

        conf = modconf.import_class('ws_controller.tests.conf.simple', 'Conf', ('DEVELOP',))

        coro = loop.create_connection(
            functools.partial(async_patterns.protocol.Protocol, loop),
            'localhost', 
            conf.PORT_SOCK)
        
        _, proto = await coro
        
        resp = await proto.write(modconf.remote.Request(conf.secret_key, 'import_class', ('ws_controller.tests.conf.simple', 'Conf', ('DEVELOP',))))

        print(resp)
        print(resp.c)
        print(resp.c.secret_key)

