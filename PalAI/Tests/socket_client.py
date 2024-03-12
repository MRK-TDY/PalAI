import json
import websocket

# The objective of this client is to purely test the connection

def on_message(ws, message):
    print(f"Received message: {json.dumps(message, indent=2)}")


def on_error(ws, error):
    print(f"Error: {error}")


def on_close(ws, close_status_code, close_msg):
    print("### Connection closed ###")


def on_open(ws):
    print("Connection opened")
    # Sending a message right after opening the connection
    ws.send(json.dumps({"prompt": "Build a very small house"}))


if __name__ == "__main__":
    # Define WebSocket endpoint
    ws_url = "ws://127.0.0.1:8000/build"


    # Create a WebSocket app/connection
    ws_app = websocket.WebSocketApp(ws_url,
                                    on_open=on_open,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close)

    # Run the WebSocket connection
    ws_app.run_forever()
