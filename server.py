import os
import yaml
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
        if request.content_type == 'application/octet-stream':
            data = request.data  # This is the raw image data
            # Generate or specify your filename here. For example:
            filename = 'received_image.png'
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            with open(file_path, 'wb') as file:
                file.write(data)

            response =  description.get_image_description()

            return jsonify({'message': 'File successfully uploaded', 'filename': response}), 200
        else:
            return jsonify({'error': 'Unsupported Media Type'}), 415


    app.run(port=PORT)
