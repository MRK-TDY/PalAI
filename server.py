import json

from flask import Flask, request, jsonify
from flask_sockets import Sockets
import yaml
import os
from configparser import RawConfigParser
import asyncio
from PalAI.Server.pal_ai import PalAI
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

app = Flask(__name__)
sockets = Sockets(app)

config = RawConfigParser()
config.read('config.ini')

PORT = config.getint('server', 'port')

with open(os.path.join(os.path.dirname(__file__), 'prompts.yaml'), 'r') as file:
    prompts_file = yaml.safe_load(file)

def create_pal_instance():
    return PalAI(prompts_file,
                config.getfloat('llm', 'temp'),
                config.get('llm', 'model_name'),
                config.get('llm', 'image_model_name'),
                config.get('openai', 'api_key'),
                config.get('llm', 'max_tokens'),
                config.getboolean('pal', 'use_images', fallback=False),
                config.getboolean('server', 'verbose'))

@sockets.route('/echo', websocket=True)
def test_connect(ws):
    while not ws.closed:
        message = ws.receive()
        if message:
            print('Client connected')
            ws.send(message)

## Is this needed
@sockets.route('/disconnect')
def test_disconnect():
    print('Client disconnected')

@sockets.route('/build')
def handle_post(ws):
    print('Client Build Request')
    while not ws.closed:
        message = ws.receive()
        print('Received message' + str(message))
        if message:
            try:
                print('Loading Json')
                json_data = json.loads(message)
                print('Building: ' + str(json_data))
                if 'prompt' in json_data:
                    pal = create_pal_instance()
                    result = asyncio.run(pal.build(json_data['prompt']))
                    result["message"] = "Data processed"
                    ws.send(json.dumps(result))
                    print('Sent Json Response: ' + str(result))
                else:
                    ws.send(json.dumps({'message': 'Missing or invalid JSON payload'}))
                    print('Missing or invalid JSON payload')
            except Exception as e:
                ws.send(json.dumps({'message': 'Error processing request', 'error': str(e)}))
                print('message: Error processing request')
        else:
            ws.send(json.dumps({'message': 'No message received'}))
            print("No message received")

if __name__ == '__main__':
    server = pywsgi.WSGIServer(('127.0.0.1', PORT), app, handler_class=WebSocketHandler)
    print(f"Running on ws://127.0.0.1:{PORT}")
    server.serve_forever()