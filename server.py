from configparser import RawConfigParser
from flask import Flask, request, jsonify
from Algorithm import dataextractor


if __name__ == '__main__':
    app = Flask(__name__)

    config = RawConfigParser()
    config.read('config.ini')

    PORT = config.getint('server', 'port')

    extractedData = {}

    @app.route('/build', methods=['POST'])
    def handle_post():
        if not request.json or 'prompt' not in request.json:
            return jsonify({'message': 'Missing or invalid JSON payload'}), 400  # Bad Request

        data = request.json['prompt']
        client_address = request.remote_addr

        result = dataextractor.extract_data(data)
        extractedData[client_address] = result

        return jsonify({'message': 'Data processed', 'result': result})

    app.run(port=PORT, debug=True)
