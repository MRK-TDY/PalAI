import json
import unittest
import subprocess
import time
import os
import signal
import asyncio
import websockets


class TestEchoWebSocket(unittest.TestCase):
    def setUp(self):
        # Start the server as a subprocess
        self.server_process = subprocess.Popen(
            ["fastapi", "dev", os.path.join(os.path.dirname(__file__), "../../server.py")]
        )
        time.sleep(10)  # Give some time for the server to start

    def test_echo(self):
        async def send_and_receive(uri, message):
            async with websockets.connect(uri) as websocket:
                await websocket.send(json.dumps(message))
                for _ in range(10):
                    response = await websocket.recv()
                    print(message, response)
                    if "result" in response:
                        return
                self.fail("Did not receive a result")


        async def test_concurrency():
            uri = "ws://127.0.0.1:8000/build"
            tasks = [send_and_receive(uri, {"prompt": "Mock prompt"}) for _ in range(5)]
            await asyncio.gather(*tasks)

        # Run the async test as a blocking call
        asyncio.run(test_concurrency())

    def tearDown(self):
        time.sleep(20)
        # # Terminate the server process
        # self.server_process.send_signal(
        #     signal.SIGINT
        # )  # Send SIGINT to allow graceful shutdown
        # self.server_process.wait(
        #     timeout=10
        # )  # Wait for up to 10 seconds for the process to exit
        #
        # # If the process has not terminated, force kill
        # if self.server_process.poll() is None:
        #     self.server_process.kill()
        #     self.server_process.wait()


if __name__ == "__main__":
    unittest.main()
