import base64
import json
import uuid
import traceback
import logging
from flask import Flask, request
from flask_sockets import Sockets
import yaml
import os
from configparser import RawConfigParser
import asyncio
from PalAI.Server.pal_ai import PalAI
from PalAI.Server.housedescription import BuildingDescriptor
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from PalAI.Server.LLMClients import (
    gpt_client,
    together_client,
    google_client,
    anyscale_client,
    local_client,
)


# Set up a directory to store uploaded images
UPLOAD_FOLDER = "Server/Uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


app = Flask(__name__)
sockets = Sockets(app)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(os.path.join(os.path.dirname(__file__), 'records.log'))
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Create a console handler to output logs to the console with INFO level
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

config = RawConfigParser()
config.read(os.path.join(os.path.dirname(__file__), "config.ini"))

PORT = config.getint("server", "port")

use_tokens = config.getboolean("server", "use_tokens")

with open(os.path.join(os.path.dirname(__file__), "prompts.yaml"), "r") as file:
    prompts_file = yaml.safe_load(file)


match config.get("llm", "type"):
    case "gpt":
        llm_client = gpt_client.GPTClient(prompts_file, logger)
    case "together":
        llm_client = together_client.TogetherClient(prompts_file, logger)
    case "google":
        llm_client = google_client.GoogleClient(prompts_file, logger)
    case "anyscale":
        llm_client = anyscale_client.AnyscaleClient(prompts_file, logger)
    case "local":
        llm_client = local_client.LocalClient(prompts_file, logger)


def create_pal_instance():
    return PalAI(prompts_file, llm_client, logger)


def create_descriptor_instance():
    return BuildingDescriptor(config.get("openai", "api_key"))


# Dictionary to keep track of active WebSocket connections
active_connections = {}
active_tasks = {}

def test_connect_token(ws):
    session_token = request.args.get('token')
    if not session_token:
        session_token = str(uuid.uuid4())
        ws.send(json.dumps({"token": session_token}))

    if session_token in active_connections:
        # Close the previous connection
        previous_ws = active_connections[session_token]
        previous_ws.close()

    active_connections[session_token] = ws

    try:
        while not ws.closed:
            message = ws.receive()
            if message:
                logger.info("Client connected")
                ws.send(message)
    except Exception as e:
        logger.error(f"Error in test_connect: {e}")
    finally:
        logger.info("WebSocket closed")
        # Remove the connection from active connections
        if session_token in active_connections and active_connections[session_token] == ws:
            del active_connections[session_token]


def test_connect_ip(ws):
    client_ip = request.remote_addr
    if client_ip in active_connections:
        # Close the previous connection
        previous_ws = active_connections[client_ip]
        previous_ws.close()

    active_connections[client_ip] = ws

    try:
        while not ws.closed:
            message = ws.receive()
            if message:
                logger.info("Client connected")
                ws.send(message)
    except Exception as e:
        logger.error(f"Error in test_connect: {e}")
    finally:
        logger.info("WebSocket closed")
        # Remove the connection from active connections
        if client_ip in active_connections and active_connections[client_ip] == ws:
            del active_connections[client_ip]

@sockets.route("/echo", websocket=True)
def test_connect(ws):
    if use_tokens:
        test_connect_token(ws)
    else:
        test_connect_ip(ws)

@sockets.route("/disconnect")
def test_disconnect():
    logger.info("Client disconnected")



async def _handle_post(ws, token):
    """Main function to handle building requests.
    Takes in a JSON with a prompt and returns a JSON with the generated building.
    """
    logger.info("Client Build Request")
    try:
        while not ws.closed:
            message = ws.receive()
            if message:
                logger.info(f"Received message: {message}")
                try:
                    json_data = json.loads(message)
                    logger.info(f"Building: {json_data}")
                    if "prompt" in json_data:
                        pal = create_pal_instance()
                        result = await pal.build(json_data["prompt"], ws)
                        result["event"] = "result"
                        result["message"] = "Data processed"
                        ws.send(json.dumps(result))
                        logger.debug(f"Sent Json Response: {result}")
                    else:
                        ws.send(json.dumps({"message": "Missing or invalid JSON payload"}))
                        logger.warning("Missing or invalid JSON payload")
                except Exception as e:
                    logger.error(f"Error processing request: {e}")
                    traceback.print_exc()
                    ws.send(json.dumps({"message": "Error processing request", "error": str(e)}))
            else:
                ws.send(json.dumps({"message": "No message received"}))
                logger.warning("No message received")
    except asyncio.CancelledError:
        logger.info("Task was cancelled")

    except Exception as e:
        logger.error(f"Error in handle_post: {e}")
    finally:
        logger.info("WebSocket closed")
        if token in active_connections and active_connections[token] == ws:
            del active_connections[token]
        if token in active_tasks:
            del active_tasks[token]
async def stop():
    loop = asyncio.get_event_loop()
    loop.stop()
    loop.close()

def handle_post_token(ws):
    session_token = request.args.get('token')
    if not session_token:
        ws.send(json.dumps({"error": "Missing session token"}))
        return

    if session_token in active_connections:
        # Close the previous connection
        previous_ws = active_connections[session_token]
        previous_ws.close()

    active_connections[session_token] = ws

    loop = asyncio.new_event_loop()
    asyncio.run(_handle_post(ws, session_token))
    #asyncio.set_event_loop(loop)
    #loop.create_task(_handle_post(ws, session_token, loop))

def handle_post_ip(ws):
    client_ip = request.remote_addr
    if client_ip in active_connections:
        # Cancel the previous task
        if client_ip in active_tasks:
            task = active_tasks[client_ip]
            if(task != None):
                task.cancel()
            else:
                del active_tasks[client_ip]

        # Close the previous connection
        previous_ws = active_connections[client_ip]
        if not previous_ws.closed:
            previous_ws.close()

    active_connections[client_ip] = ws
    loop = asyncio.get_event_loop()
    if loop.is_running():
        task = loop.create_task(_handle_post(ws, client_ip))
    else:
        task = loop.run_until_complete(_handle_post(ws, client_ip))
    active_tasks[client_ip] = task

    # logger.error(f"Error in task management: {e}")

#except Exception as e:
    #    logger.error(f"Error in handle_post: {e}")

    #loop.create_task(_handle_post(ws, client_ip, loop))

@sockets.route("/build")
def handle_post(ws):
    if(use_tokens):
        #test_connect_token(ws)
        handle_post_token(ws)
    else:
        handle_post_ip(ws)



if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    server = pywsgi.WSGIServer(("0.0.0.0", PORT), app, handler_class=WebSocketHandler)
    logger.info(f"Running on ws://0.0.0.0:{PORT}")
    server.serve_forever()
