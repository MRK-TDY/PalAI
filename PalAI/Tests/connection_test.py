import json
import unittest
import subprocess
import time
import os
import signal
import asyncio
import websockets
import select


class TestEchoWebSocket(unittest.TestCase):
    def setUp(self):
        env = os.environ.copy()
        env["CONFIG_PATH"] = "config.mock.ini"
        self.server_process = subprocess.Popen(
            [
                "fastapi",
                "dev",
                os.path.join(os.path.dirname(__file__), "../../server.py"),
            ],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd=os.path.dirname(os.path.dirname(__file__)),
        )

        startup_message = "Started server process"
        timeout = 30  # 30 seconds timeout
        start_time = time.time()

        while True:
            # Use select to wait for output with a timeout
            ready, _, _ = select.select(
                [self.server_process.stdout, self.server_process.stderr], [], [], 0.1
            )
            for stream in ready:
                line = stream.readline()
                if line:
                    print(line.strip())  # Print each line for debugging
                    if startup_message in line:
                        return  # Server has started

            # Check if the process has ended
            if self.server_process.poll() is not None:
                raise RuntimeError("Server process ended unexpectedly")

            # Check for timeout
            if time.time() - start_time > timeout:
                self.server_process.terminate()
                raise TimeoutError("Server startup timed out")

            time.sleep(0.1)  # Short sleep to prevent busy-waiting

    def test_echo(self):
        async def send_and_receive(uri, message):
            async with websockets.connect(uri) as websocket:
                await websocket.send(message)
                for _ in range(50):
                    response = await websocket.recv()
                    print(message, response)
                    if "result" in response:
                        return
                self.fail("Did not receive a result")

        async def test_concurrency():
            uri = "ws://127.0.0.1:8000/build"
            tasks = [
                send_and_receive(uri, json.dumps({"prompt": "test prompt"}))
                for _ in range(5)
            ]
            await asyncio.gather(*tasks)

        # Run the async test as a blocking call
        asyncio.run(test_concurrency())

    def tearDown(self):
        # Terminate the server process
        self.server_process.send_signal(
            signal.SIGINT
        )  # Send SIGINT to allow graceful shutdown
        self.server_process.wait(
            timeout=10
        )  # Wait for up to 10 seconds for the process to exit

        # If the process has not terminated, force kill
        if self.server_process.poll() is None:
            self.server_process.kill()
            self.server_process.wait()


if __name__ == "__main__":
    unittest.main()
