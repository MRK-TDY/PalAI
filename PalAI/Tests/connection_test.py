import unittest
import subprocess
import time
import os
import signal

class TestEchoWebSocket(unittest.TestCase):
    def setUp(self):
        # Start the server as a subprocess
        self.server_process = subprocess.Popen(['python', os.path.join(os.path.dirname(__file__), '../../server.py')])
        time.sleep(5)  # Give some time for the server to start

    @unittest.skip("This fails on some systems for package mismatch reasons")
    def test_echo(self):
        # Connect to the WebSocket server
        import websocket
        ws = websocket.WebSocket()
        try:
            ws.connect("ws://127.0.0.1:8000/echo")  # Adjust the port if needed
            test_message = "Test"
            ws.send(test_message)
            received_message = ws.recv()

            # Assert that the received message is the same as the sent message
            self.assertEqual(received_message, test_message)
        finally:
            # Ensure the WebSocket is closed after the test
            ws.close()

    def tearDown(self):
        # Terminate the server process
        self.server_process.send_signal(signal.SIGINT)  # Send SIGINT to allow graceful shutdown
        self.server_process.wait(timeout=10)  # Wait for up to 10 seconds for the process to exit

        # If the process has not terminated, force kill
        if self.server_process.poll() is None:
            self.server_process.kill()
            self.server_process.wait()

if __name__ == '__main__':
    unittest.main()

