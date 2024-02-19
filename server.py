import os
import yaml
from configparser import RawConfigParser
from flask import Flask, request, jsonify
from Server.pal_ai import PalAI

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


    @app.route('/build', methods=['POST'])
    def handle_post():
        if not request.json or 'prompt' not in request.json:
            return jsonify({'message': 'Missing or invalid JSON payload'}), 400  # Bad Request

        prompt = request.json['prompt']
        response = pal.get_llm_response(*pal.format_prompt(prompt))
        result = pal.extract_building_information(response)

        return jsonify({'message': 'Data processed', 'result': result})


    app.run(port=PORT)
