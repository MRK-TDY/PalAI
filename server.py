import os
import yaml
import asyncio
from configparser import RawConfigParser
from flask import Flask
from flask_socketio import SocketIO
from PalAI.Server.pal_ai import PalAI

if __name__ == '__main__':
    app = Flask(__name__)
    socketio = SocketIO(app, cors_allowed_origins="*")

    config = RawConfigParser()
    config.read('config.ini')

    PORT = config.getint('server', 'port')

    with open(os.path.join(os.path.dirname(__file__), 'prompts.yaml'), 'r') as file:
        prompts_file = yaml.safe_load(file)



    @socketio.on('connect')
    def test_connect():
        print('Client connected')

    @socketio.on('disconnect')
    def test_disconnect():
        print('Client disconnected')

    @socketio.on('build')
    def handle_post(json):
        if not json or 'prompt' not in json:
            socketio.emit('message', 'Missing or invalid JSON payload') # Bad Request
            return

        pal = PalAI(prompts_file,
                    config.getfloat('llm', 'temp'),
                    config.get('llm', 'model_name'),
                    config.get('llm', 'image_model_name'),
                    config.get('openai', 'api_key'),
                    config.get('llm', 'max_tokens'),
                    config.getboolean('pal', 'use_images', fallback=False),
                    config.getboolean('server', 'verbose'))

        prompt = json['prompt']
        result = asyncio.run(pal.build(prompt, socketio))
        result["message"] = "Data processed"

        socketio.emit("response", result)
        socketio.emit("disconnect")
        return

    socketio.run(app, port=PORT)
