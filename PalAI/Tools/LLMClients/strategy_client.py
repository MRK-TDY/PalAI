import os
import json
from PalAI.Server.LLMClients.llm_client import LLMClient
from hypothesis import strategies as st
from loguru import logger

class StrategyClient(LLMClient):

    def __init__(self, prompts_file, **kwargs):
        LLMClient.__init__(self, prompts_file)
        self.draw = kwargs.get('draw', None)
        if self.draw is None:
            raise ValueError("Must set strategy draw.")

        # self.model_name = self.config.get('openai', 'model_name')
        self.price_rate = 0

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
        self.layer_count = self.draw(st.integers(min_value=1, max_value=7))
        response = ""
        for i in range(self.layer_count):
            response += f"Layer {i}: {self.draw(st.sampled_from(self.layers))}\n"

        return response

    def get_add_ons_response(self):
        response = ""
        for i in range(self.layer_count):
            response += f"Layer {i}: {self.draw(st.sampled_from(self.window_styles))} | {self.draw(st.sampled_from(self.window_quantifiers))}\n"
        return response

    def get_materials_response(self):
        response = "FLOOR:Sand\nINTERIOR:Sand\nEXTERIOR:Sand\nSTYLE:"
        response += self.draw(st.sampled_from(self.styles))
        return response


    async def get_agent_response(self, agent, prompt, **kwargs):
        match agent:
            case LLMClient.ARCHITECT:
                return f"{self.get_architect_response()}"
            case LLMClient.MATERIALS:
                return "FLOOR:Sand\nINTERIOR:Sand\nEXTERIOR:Sand\nSTYLE:modern"
            case LLMClient.ADD_ONS:
                return self.get_add_ons_response()
            case _:
                return "Layer 0: Single block"


    async def get_llm_response(self, system_message, prompt, **kwargs):
        raise NotImplementedError("The mock client does not support the get_llm_response method")

