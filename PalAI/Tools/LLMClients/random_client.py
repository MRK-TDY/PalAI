import os
import random
import json
from PalAI.Server.LLMClients.llm_client import LLMClient
from loguru import logger


class RandomClient(LLMClient):

    def __init__(self, prompts_file, **kwargs):
        LLMClient.__init__(self, prompts_file)

        # self.model_name = self.config.get('openai', 'model_name')
        self.price_rate = 0
        self.rng = kwargs.get('rng', random.Random())

        # get lists based on jsons
        with open(os.path.join(os.path.dirname(__file__), '../../Server/layers.json'), 'r') as f:
            aux = json.load(f)
            self.layers = [i["name"] for i in aux['layers']]

        with open(os.path.join(os.path.dirname(__file__), '../../Server/styles.json'), 'r') as f:
            aux = json.load(f)
            self.styles = [i for i in aux['styles'].keys()]

        with open(os.path.join(os.path.dirname(__file__), '../../Server/windows.json'), 'r') as f:
            aux = json.load(f)
            self.window_styles = [i["name"] for i in aux['styles']]
            self.window_quantifiers = [i["name"] for i in aux['quantifiers']]

    def get_architect_response(self):
        self.layer_count = max(1, int(self.rng.gauss(4, 2)))
        response = ""
        for i in range(self.layer_count):
            response += f"Layer {i}: {self.rng.choice(self.layers)}\n"

        return response

    def get_add_ons_response(self):
        response = ""
        for i in range(self.layer_count):
            response += f"Layer {i}: {self.rng.choice(self.window_styles)} | {self.rng.choice(self.window_quantifiers)}\n"
        return response


    async def get_agent_response(self, agent, prompt, **kwargs):
        match agent:
            case LLMClient.ARCHITECT:
                return f"We will create a building made up of 3 layers.\n {self.get_architect_response()}"
            case LLMClient.MATERIALS:
                return "FLOOR:Sand\nINTERIOR:Sand\nEXTERIOR:Sand\nSTYLE:modern"
            case LLMClient.ADD_ONS:
                return self.get_add_ons_response()
            case _:
                return "Layer 0: Single block"


    async def get_llm_response(self, system_message, prompt, **kwargs):
        raise NotImplementedError("The mock client does not support the get_llm_response method")

