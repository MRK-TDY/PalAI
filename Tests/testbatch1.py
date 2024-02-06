import unittest
import requests

class TestBuildEndpoint(unittest.TestCase):

    SERVER_URL = "http://127.0.0.1:8000"
    BUILD_ENDPOINT = "/build"

    def test_post_with_prompt(self):
        payload = {"prompt": "I want a house with an M shape."}
        response = requests.post(self.SERVER_URL + self.BUILD_ENDPOINT, json=payload)
        data = response.json()

        self.assertEqual(data['message'], 'Data processed')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
