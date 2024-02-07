import json
import unittest
import requests
from Server.visualizer import *
class TestClient(unittest.TestCase):

    SERVER_URL = "http://127.0.0.1:8000"
    BUILD_ENDPOINT = "/build"

    def test_server(self, prompt, file_name):
        payload = {"prompt": prompt}
        response = requests.post(self.SERVER_URL + self.BUILD_ENDPOINT, json=payload)
        data = response.json()

        print("Response: \n" + str(json.dumps(data, sort_keys=True, indent=4)))
        obj = ObjVisualizer().generate_obj(data['result'])
        with open(f'{file_name}.obj', 'w') as file:
            file.write(obj)

        self.assertEqual(data['message'], 'Data processed')
        self.assertEqual(response.status_code, 200)

    def test_post_with_prompt(self):
        self.test_server("Generate a building in the shape of stairs", "stairs")
        self.test_server("Generate a building in the shape of an L", "L-shape")
        self.test_server("Generate a building in the shape of an M", "M-shape")

if __name__ == '__main__':
    unittest.main()
