# This is a sample Python script.
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

from http.server import BaseHTTPRequestHandler
import socketserver
import logging
from PalAI.Algorithm import dataextractor

#Change Port if needed
PORT = 8000

extractedData = {}

OutputPath = {}


# Server Handler
class ServerHandler(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text')
        self.end_headers()

    # Handle GET requests
    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        print(str(self.headers))

        content_length = int(self.headers['Content-Length'])   # <--- Gets the size of data
        type = self.headers.get_content_type()
        self._set_response()
        if (len(extractedData) > 0):
            post_data = self.rfile.read(content_length)  # <--- Gets the data itself
            data = post_data.decode('utf-8')
            #self.wfile.write(bytes(extractedData[self.client_address[0]], encoding="utf-8"))
            self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

        else:
            self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

    # Handle POST requests
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        post_data = self.rfile.read(content_length)  # <--- Gets the data itself
        data = post_data.decode('utf-8')
        self._set_response()
        self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))
        if (len(data) > -1):

            ## Saving Data to an Array
            extractedData[self.client_address[0]] = data

            ##Extract Data
            dataextractor.extract_data(data)

Handler = ServerHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()