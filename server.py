import base64
import json

import traceback
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



# Set up a directory to store uploaded images
UPLOAD_FOLDER = 'Server/Uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)



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

def create_descriptor_instance():
    return BuildingDescriptor(config.get('openai', 'api_key'))

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
                json_data = json.loads(message)
                print('Building: ' + str(json_data))
                if 'prompt' in json_data:
                    pal = create_pal_instance()
                    result = asyncio.run(pal.build(json_data['prompt'], ws))
                    result["message"] = "Data processed"
                    ws.send(json.dumps(result))
                    print('Sent Json Response: ' + str(result))
                else:
                    ws.send(json.dumps({'message': 'Missing or invalid JSON payload'}))
                    print('Missing or invalid JSON payload')
            except Exception as e:
                traceback.print_exc()
                ws.send(json.dumps({'message': 'Error processing request', 'error': str(e)}))
                print('message: Error processing request')
        else:
            ws.send(json.dumps({'message': 'No message received'}))
            print("No message received")

@sockets.route('/description')
def handle_post(ws):
    print('Client Build Request')
    while not ws.closed:
        message = ws.receive()
        print('Received message' + str(message))
        if message:
            try:
                json_object = json.loads(message)
                # Generate or specify your filename here. For example:
                filenameFront = 'front.png'
                filenameRight = 'right.png'
                filenameLeft = 'left.png'
                filenameBack = 'back.png'

                file_path = os.path.join(UPLOAD_FOLDER, filenameFront)
                imgdata = base64.b64decode(json_object["front"])
                with open(file_path, 'wb') as fileFront:
                    fileFront.write(imgdata)

                file_path = os.path.join(UPLOAD_FOLDER, filenameRight)
                imgdata = base64.b64decode(json_object["right"])
                with open(file_path, 'wb') as fileRight:
                    fileRight.write(imgdata)

                file_path = os.path.join(UPLOAD_FOLDER, filenameLeft)
                imgdata = base64.b64decode(json_object["left"])
                with open(file_path, 'wb') as fileLeft:
                    fileLeft.write(imgdata)

                file_path = os.path.join(UPLOAD_FOLDER, filenameBack)
                imgdata = base64.b64decode(json_object["back"])
                with open(file_path, 'wb') as fileBack:
                    fileBack.write(imgdata)

                descriptor = create_descriptor_instance()
                response = descriptor.get_image_description()
                ws.send(json.dumps(response))
                print('Sent Json Response: ' + str(response))

            except Exception as e:
                traceback.print_exc()
                ws.send(json.dumps({'message': 'Error processing request', 'error': str(e)}))
                print('message: Error processing request')


if __name__ == '__main__':
    server = pywsgi.WSGIServer(('127.0.0.1', PORT), app, handler_class=WebSocketHandler)
    print(f"Running on ws://127.0.0.1:{PORT}")
    server.serve_forever()
