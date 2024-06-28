import base64
import json
import random
import uuid
import sys
import traceback
from loguru import logger
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

fmt = "{time} - {name} - {level} - {message}"
logger.add("records.log", level="DEBUG", format=fmt)
logger.add(sys.stderr, level="ERROR", format=fmt)
# logger.add(sys.stdout, level="INFO", format=fmt)

config = RawConfigParser()
config.read(os.path.join(os.path.dirname(__file__), "config.ini"))

PORT = config.getint("server", "port")

use_tokens = config.getboolean("server", "use_tokens")

with open(os.path.join(os.path.dirname(__file__), "prompts.yaml"), "r") as file:
    prompts_file = yaml.safe_load(file)


match config.get("llm", "type"):
    case "gpt":
        llm_client = gpt_client.GPTClient(prompts_file)
    case "together":
        llm_client = together_client.TogetherClient(prompts_file)
    case "google":
        llm_client = google_client.GoogleClient(prompts_file)
    case "anyscale":
        llm_client = anyscale_client.AnyscaleClient(prompts_file)
    case "local":
        llm_client = local_client.LocalClient(prompts_file)
    case "random":
        llm_client = random_client.RandomClient(prompts_file)
    case "mock":
        llm_client = mock_client.MockClient(prompts_file)


def create_pal_instance():
    return PalAI(prompts_file, llm_client)


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

    return app


logger.info(f"Running on 0.0.0.0:{PORT}")
api = create_app()
