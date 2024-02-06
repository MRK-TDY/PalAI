from configparser import RawConfigParser
from flask import Flask, request, jsonify
from Algorithm.dataextractor import *
from Server.gptlink import GPTHandler

if __name__ == '__main__':
    app = Flask(__name__)

    config = RawConfigParser()
    config.read('config.ini')

    PORT = config.getint('server', 'port')

    gpt_handler = GPTHandler(config)

    extractedData = {}

    @app.route('/build', methods=['POST'])
    def handle_post():
        if not request.json or 'prompt' not in request.json:
            return jsonify({'message': 'Missing or invalid JSON payload'}), 400  # Bad Request

        prompt = request.json['prompt']
        client_address = request.remote_addr

        result = gpt_handler.get_building_data(prompt)
        extractedData[client_address] = result

        return jsonify({'message': 'Data processed', 'result': result})

    app.run(port=PORT)
