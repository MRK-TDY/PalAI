import threading
import os
import websocket
import json
from PalAI.Server.visualizer import ObjVisualizer

# URL of the WebSocket you want to connect to
ws_url = "ws://3.75.151.242:5005/build"
ws_url = "ws://0.0.0.0:8000/build"


# Define the function to connect to the WebSocket and send/receive messages
def connect_and_send(ws_url, message, thread_id):
    def on_message(ws, message):
        print(f"Thread {thread_id}: Response - {message}")
        message = json.loads(message)
        if "result" in message:

            obj = ObjVisualizer().generate_obj(message["result"])

            with open(
                os.path.join(os.path.dirname(__file__), f"thread_{thread_id}.obj"), "w"
            ) as fptr:
                fptr.write(obj)
                fptr.flush()

            ws.close()

    def on_error(ws, error):
        print(f"Thread {thread_id}: Error - {error}")

    def on_close(ws, close_status_code, close_msg):
        print(f"Thread {thread_id}: Closed Connection")

    def on_open(ws):
        print(f"Thread {thread_id}: Connection Opened")
        ws.send(json.dumps(message))

    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    ws.run_forever()


# The request message you want to send
request_message = {"prompt": "I want a tiny house"}

# Number of parallel threads you want to create
num_threads = 2

# Creating and starting threads
threads = []
for i in range(num_threads):
    thread = threading.Thread(
        target=connect_and_send, args=(ws_url, request_message, i)
    )
    thread.start()
    threads.append(thread)

# Joining threads to ensure they complete before the main script ends
for thread in threads:
    thread.join()
