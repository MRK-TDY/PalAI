import json
import unittest
import subprocess
import time
import os
import signal
import asyncio
import websockets
import select

from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs


class TestEchoWebSocket(unittest.TestCase):
    def setUp(cls):
        cls.container = DockerContainer("palai:latest").with_env("CONFIG_PATH", "config.mock.ini").with_exposed_ports(8000)
        cls.container.start()
        wait_for_logs(cls.container, ".*Application startup complete.*\\n", 30)
        cls.ws_uri = f"ws://{cls.container.get_container_host_ip()}:{cls.container.get_exposed_port(8000)}"
        cls.port = cls.container.get_exposed_port(8000)


    def test_echo(self):
        async def send_and_receive(uri, message):
            async with websockets.connect(uri) as websocket:
                await websocket.send(message)
                for _ in range(50):
                    response = await websocket.recv()
                    # print(message, response)
                    if "result" in response:
                        return
                self.fail("Did not receive a result")

        async def test_concurrency():
            uri = f"ws://127.0.0.1:{self.port}/build"
            tasks = [
                send_and_receive(uri, json.dumps({"prompt": "test prompt"}))
                for _ in range(5)
            ]
            await asyncio.gather(*tasks)

        # Run the async test as a blocking call
        asyncio.run(test_concurrency())


if __name__ == "__main__":
    unittest.main()
