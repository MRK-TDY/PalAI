import base64
import requests
import openai


pathFront = "Server/Uploads/front.png"
pathRight = "Server/Uploads/right.png"
pathLeft = "Server/Uploads/left.png"
pathBack = "Server/Uploads/back.png"

class BuildingDescriptor():
    def __init__(self, api_key):
        self.api_key = api_key

    def encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')


    def get_image_description(self):
        base64_imageFront = self.encode_image(pathFront)
        base64_imageRight = self.encode_image(pathRight)
        base64_imageLeft = self.encode_image(pathLeft)
        base64_imageBack = self.encode_image(pathBack)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "The following images show a building from the front, right, left and back.Please describe this building style in a few worlds. Don't mention the pictures"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_imageFront}"
                            }
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_imageRight}"
                            }
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_imageLeft}"
                            }
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_imageBack}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 300
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        print(response.json()['choices'][0]['message']['content'])
        return response.json()['choices'][0]['message']['content']
