import os
import yaml
import asyncio
from configparser import RawConfigParser
from flask import Flask, request, jsonify
from PalAI.Server.pal_ai import PalAI

if __name__ == '__main__':
    app = Flask(__name__)

    config = RawConfigParser()
    config.read('config.ini')

    PORT = config.getint('server', 'port')

    with open(os.path.join(os.path.dirname(__file__), 'prompts.yaml'), 'r') as file:
        prompts_file = yaml.safe_load(file)



    @app.route('/build', methods=['POST'])
    def handle_post():
        if not request.json or 'prompt' not in request.json:
            return jsonify({'message': 'Missing or invalid JSON payload'}), 400  # Bad Request

        pal = PalAI(prompts_file,
                    config.getfloat('llm', 'temp'),
                    config.get('llm', 'model_name'),
                    config.get('llm', 'image_model_name'),
                    config.get('openai', 'api_key'),
                    config.get('llm', 'max_tokens'),
                    config.getboolean('pal', 'use_images', fallback=False),
                    config.getboolean('server', 'verbose'))

        prompt = request.json['prompt']
        result = asyncio.run(pal.build(prompt))
        result["message"] = "Data processed"

        return jsonify(result)

    app.run(port=PORT)
