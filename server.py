import os
import yaml
import json
import base64
from configparser import RawConfigParser
from flask import Flask, request, jsonify
from Server.pal_ai import PalAI
from Server.housedescription import BuildingDescriptor


# Set up a directory to store uploaded images
UPLOAD_FOLDER = 'Server/Uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


if __name__ == '__main__':
    app = Flask(__name__)

    config = RawConfigParser()
    config.read('config.ini')

    PORT = config.getint('server', 'port')

    with open(os.path.join(os.path.dirname(__file__), 'prompts.yaml'), 'r') as file:
        prompts_file = yaml.safe_load(file)

    pal = PalAI(prompts_file,
                config.getfloat('llm', 'temp'),
                config.get('llm', 'model_name'),
                config.get('openai', 'api_key'),
                config.get('llm', 'max_tokens'),
                config.getboolean('server', 'verbose'))

    description = BuildingDescriptor(config.get('openai', 'api_key'))

    @app.route('/build', methods=['POST'])
    def handle_post():
        if not request.json or 'prompt' not in request.json:
            return jsonify({'message': 'Missing or invalid JSON payload'}), 400  # Bad Request
        print("Received Build request")
        prompt = request.json['prompt']
        response = pal.get_llm_response(*pal.format_prompt(prompt))
        result = pal.extract_building_information(response)

        return jsonify({'message': 'Data processed', 'result': result})


    @app.route('/description', methods=['POST'])
    def handle_image_post():
        if request.content_type == 'application/json':
            data = request.data  # This is the raw image data
            # Generate or specify your filename here. For example:
            filenameFront = 'front.png'
            filenameRight = 'right.png'
            filenameLeft = 'left.png'
            filenameBack = 'back.png'

            json_object = json.loads(data)

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

            response = description.get_image_description()
            return jsonify({'message': response}), 200
        else:
            return jsonify({'error': 'Unsupported Media Type'}), 415


    app.run(port=PORT)
