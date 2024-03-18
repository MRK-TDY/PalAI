import json
from datetime import datetime
import unittest
import requests
import os
import csv
import yaml
import asyncio

from PalAI.Server.visualizer import *
from PalAI.Server.pal_ai import PalAI

class TestClient(unittest.TestCase):

    def _test_server(self, prompt, file_name, path=""):
        with open(os.path.join(os.path.dirname(__file__), '../../prompts.yaml'), 'r') as file:
            prompts_file = yaml.safe_load(file)

        pal = PalAI(prompts_file,
                    "gpt")
        api_response = asyncio.run(pal.build(prompt))

        print("Response: \n" + str(json.dumps(api_response, sort_keys=True, indent=4)))
        obj = ObjVisualizer().generate_obj(api_response['result'])

        #ensure path exists
        if not os.path.exists(f'{path}'):
            os.makedirs(f'{path}')
        file_path = f'{path}/{file_name}'
        with open(file_path + ".obj", 'w') as file:
            file.write(obj)
        with open(file_path + ".txt", 'w') as file:
            file.write(json.dumps(api_response, indent=2))

        self.assertIn("result", api_response.keys())

    @classmethod
    def setUpClass(cls):
        now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        cls.path = f"Logs/{now}"

    def test_single(self):
        self._test_server("Generate a small 3x3 house with a single block on the top floor", "demo", self.path)


    # def test_small_batch(self):
    #     self._test_server("Generate a building in the shape of stairs", "stairs", self.path)
    #     self._test_server("Generate a building in the shape of an M", "M-shape", self.path)
    #
    # def test_csv_prompts(self):
    #     with open(os.path.join(os.path.dirname(__file__), 'prompts.csv'), 'r') as csvfile:
    #         reader = csv.DictReader(csvfile, delimiter=';')
    #         for row in reader:
    #             self._test_server(row["PROMPT"], row["PATH"], self.path)

if __name__ == '__main__':
    unittest.main()
