import base64
import json

import traceback
import logging
from flask import Flask
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



@sockets.route("/echo")
def test_connect(ws):
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


@sockets.route("/disconnect")
def test_disconnect():
    logger.info("Client disconnected")



async def _handle_post(ws):
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
    except Exception as e:
        logger.error(f"Error in handle_post: {e}")
    finally:
        logger.info("WebSocket closed")

@sockets.route("/build")
def handle_post(ws):
    """Main function to handle building requests.
    Takes in a JSON with a prompt and returns a JSON with the generated building.
    """
    asyncio.run(_handle_post(ws))



if __name__ == "__main__":
    server = pywsgi.WSGIServer(("0.0.0.0", PORT), app, handler_class=WebSocketHandler)
    logger.info(f"Running on ws://0.0.0.0:{PORT}")
    server.serve_forever()
