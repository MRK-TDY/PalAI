import asyncio
import json
import os
import sys
import traceback
import uuid
from configparser import RawConfigParser
from contextlib import asynccontextmanager

import sentry_sdk
import yaml
from fastapi import APIRouter, FastAPI, WebSocket, WebSocketDisconnect
from loguru import logger
from sentry_sdk.integrations.loguru import LoggingLevels, LoguruIntegration

from PalAI.Server.LLMClients import gpt_client
from PalAI.Server.pal_ai import PalAI
from PalAI.Server.utils import log_additional_data
from PalAI.Tools.LLMClients import mock_client, random_client

# Set up a directory to store uploaded images
UPLOAD_FOLDER = "Server/Uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

config_path = os.getenv("CONFIG_PATH", "config.ini")
config = RawConfigParser()
config.read(os.path.join(os.path.dirname(__file__), config_path))

router = APIRouter()

# Set up logger
fmt = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "{extra[request_id]} |"
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
logger.remove(0)
logger.configure(extra={"request_id": "NONE"})
logger.add(
    os.path.join(
        os.path.dirname(
            __file__,
        ),
        "records.log",
    ),
    level="DEBUG",
    format=fmt,
)
logger.add(sys.stderr, level="ERROR", format=fmt, colorize=True)
logger.add(sys.stdout, level="INFO", format=fmt, colorize=True)

# Set up Sentry
dsn = config.get("sentry", "dsn", fallback=None)
if dsn is not None:
    try:
        sentry_loguru = LoguruIntegration(
            level=LoggingLevels.INFO.value,  # Capture info and above as breadcrumbs
            event_level=LoggingLevels.ERROR.value,  # Send errors as events
        )

        sentry_sdk.init(
            dsn=dsn,
            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for performance monitoring.
            traces_sample_rate=1.0,
            # Set profiles_sample_rate to 1.0 to profile 100%
            # of sampled transactions.
            # We recommend adjusting this value in production.
            profiles_sample_rate=1.0,
            send_default_pii=True,  # necessary to include prompts
            enable_tracing=True,
            integrations=[sentry_loguru],
        )

        logger.info("Sentry initialized")
    except:
        logger.warning("Failed to initialize Sentry")
        pass


logger.info("Using config file: " + config_path)
PORT = config.getint("server", "port")

use_tokens = config.getboolean("server", "use_tokens")

with open(os.path.join(os.path.dirname(__file__), "prompts.yaml"), "r") as file:
    prompts_file = yaml.safe_load(file)


match config.get("llm", "type", fallback="gpt"):
    case "random":
        llm_client = random_client.RandomClient(prompts_file)
    case "mock":
        llm_client = mock_client.MockClient(prompts_file)
    case "gpt" | _:
        llm_client = gpt_client.GPTClient(prompts_file)



def create_pal_instance():
    return PalAI(prompts_file, llm_client)


@router.get("/echo")
def test_connect():
    return "200 - ok"


async def stop():
    loop = asyncio.get_event_loop()
    loop.stop()
    loop.close()


@router.websocket("/build")
async def build(ws: WebSocket):
    logger.info("Client connected")
    await manager.connect(ws)
    # Increment a counter by one for each button click.
    sentry_sdk.metrics.incr(key="Pal Connection", value=1, tags={"service": "PALAI"})

    while True:
        with sentry_sdk.start_transaction(op="build-request", name="build-request"):
            try:
                message = await ws.receive_text()
                sentry_sdk.metrics.incr(
                    key="Pal Request", value=1, tags={"service": "PALAI"}
                )

                if message:
                    id = str(uuid.uuid4())
                    try:
                        json_data = json.loads(message)
                        id = json_data.get("id", id)

                        if "prompt" not in json_data or len(json_data["prompt"]) < 3:
                            logger.warning("Missing or invalid JSON payload")
                            continue

                        for key, value in json_data.items():
                            log_additional_data(key, str(value))

                        logger.info(f"PalAI request {id}: {json_data['prompt']}")
                        pal = create_pal_instance()

                        with logger.contextualize(request_id=id):
                            result = await pal.build(
                                prompt=json_data["prompt"],
                                materials=json_data.get("materials", None),
                                decorations=json_data.get("decorations", None),
                                ws=ws,
                                manager=manager,
                            )
                        result["event"] = "result"
                        result["message"] = "Data processed"
                        await manager.send_personal_message(json.dumps(result), ws)

                        logger.info(f"Request {id}: success")
                    except Exception as e:
                        logger.error(f"Error processing request {id}: {e}")
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
                logger.info("Client closed connection")
                return


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


logger.info(f"PalAI server started on port {PORT}")
api = create_app()
