import base64
import json
import random
import uuid
import traceback
import logging
import yaml
import os
from configparser import RawConfigParser
import asyncio
from PalAI.Server.pal_ai import PalAI
from PalAI.Server.housedescription import BuildingDescriptor
from fastapi import FastAPI
from PalAI.Server.LLMClients import (
    gpt_client,
    together_client,
    google_client,
    anyscale_client,
    local_client,
)
from PalAI.Tools.LLMClients import random_client, mock_client
from contextlib import asynccontextmanager
from fastapi import APIRouter, WebSocket, WebSocketDisconnect


# Set up a directory to store uploaded images
UPLOAD_FOLDER = "Server/Uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
router = APIRouter()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(
    os.path.join(os.path.dirname(__file__), "records.log")
)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Create a console handler to output logs to the console with INFO level
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(levelname)s - %(message)s")
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
    case "random":
        llm_client = random_client.RandomClient(prompts_file, logger)
    case "mock":
        llm_client = mock_client.MockClient(prompts_file, logger)


def create_pal_instance():
    return PalAI(prompts_file, llm_client, logger)


def create_descriptor_instance():
    return BuildingDescriptor(config.get("openai", "api_key"))


@router.get("/echo")
def test_connect():
    return "200 - ok"


async def _handle_post(ws, token):
    """Main function to handle building requests.
    Takes in a JSON with a prompt and returns a JSON with the generated building.
    """


async def stop():
    loop = asyncio.get_event_loop()
    loop.stop()
    loop.close()


@router.websocket("/build")
async def handle_post(ws: WebSocket):
    logger.info("PalAI WebSocket connected")
    await manager.connect(ws)

    try:
        message = await ws.receive_text()
        if message:
            logger.info(f"Received message: {message}")
            try:
                json_data = json.loads(message)
                logger.info(f"Building: {json_data}")
                if "prompt" in json_data and len(json_data["prompt"]) > 3:
                    pal = create_pal_instance()
                    result = await pal.build(json_data["prompt"], ws, manager)
                    result["event"] = "result"
                    result["message"] = "Data processed"
                    await manager.send_personal_message(json.dumps(result), ws)

                    logger.debug(f"Sent Json Response: {result}")
                else:
                    await manager.send_personal_message(
                        json.dumps({"message": "Missing or invalid JSON payload"}), ws
                    )
                    logger.warning("Missing or invalid JSON payload")
            except Exception as e:
                logger.error(f"Error processing request: {e}")
                traceback.print_exc()
                await manager.send_personal_message(
                    json.dumps(
                        {"message": "Error processing request", "error": str(e)}
                    ),
                    ws,
                )
        else:
            await manager.send_personal_message(
                json.dumps({"message": "No message received"}), ws
            )
            logger.warning("No message received")

    except WebSocketDisconnect:
        manager.disconnect(ws)

    finally:
        logger.info("WebSocket closed")


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # logger.info("Starting up...")
    # logger.info("Started up")
    # app.state.pal = create_pal_instance()
    # logger.info("Shutting down...")
    yield


def create_app():
    app = FastAPI(lifespan=lifespan)

    app.include_router(router)
    # app.include_router(search_router)
    # app.include_router(websocket_chat_router)

    loop = asyncio.get_event_loop()

    return app


logger.info(f"Running on 0.0.0.0:{PORT}")
api = create_app()
