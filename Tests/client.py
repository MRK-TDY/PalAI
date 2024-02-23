import json
from datetime import datetime
import unittest
import requests
from Server.visualizer import *
import csv
class TestClient(unittest.TestCase):

    SERVER_URL = "http://127.0.0.1:8000"
    BUILD_ENDPOINT = "/build"

    def _test_server(self, prompt, file_name, path=""):
        payload = {"prompt": prompt}
        response = requests.post(self.SERVER_URL + self.BUILD_ENDPOINT, json=payload)
        data = response.json()

        print("Response: \n" + str(json.dumps(data, sort_keys=True, indent=4)))
        obj = ObjVisualizer().generate_obj(data['result'])

        #ensure path exists
        if not os.path.exists(f'{path}'):
            os.makedirs(f'{path}')
        file_path = f'{path}/{file_name}.obj'
        with open(file_path, 'w') as file:
            file.write(obj)

        try:
           os.startfile(file_path)
        except Exception as e:
            pass  # Ignore error

        self.assertEqual(data['message'], 'Data processed')
        self.assertEqual(response.status_code, 200)

    @classmethod
    def setUpClass(cls):
        now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        cls.path = f"Logs/{now}"

    def test_single(self):
        self._test_server("Generate a tower that is 3 blocks wide and tapers at the top, the tower should be place at 5,5", "demo", self.path)


    def test_small_batch(self):
        self._test_server("Generate a building in the shape of stairs", "stairs", self.path)
        self._test_server("Generate a building in the shape of an M", "M-shape", self.path)

    def test_csv_prompts(self):
        with open(os.path.join(os.path.dirname(__file__), 'prompts.csv'), 'r') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            for row in reader:
                self._test_server(row["PROMPT"], row["PATH"], self.path)

if __name__ == '__main__':
    unittest.main()
