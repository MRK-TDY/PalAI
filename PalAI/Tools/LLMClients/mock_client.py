from PalAI.Server.LLMClients.llm_client import LLMClient
from loguru import logger

class MockClient(LLMClient):

    def __init__(self, prompts_file, **kwargs):
        LLMClient.__init__(self, prompts_file)

        # self.model_name = self.config.get('openai', 'model_name')
        self.price_rate = 0

    async def get_agent_response(self, agent, prompt, **kwargs):
        match agent:
            case LLMClient.ARCHITECT:
                return "We will create a building made up of 3 layers.\nLayer 0: 5x5 square\nLayer 1: small cross\nLayer 2: single cube\n"
            case LLMClient.BRICKLAYER:
                return "B:CUBE|0,0\nB:CUBE|0,1\nB:CUBE|1,0\nB:CUBE|1,1\n"
            case LLMClient.MATERIALS:
                return "FLOOR:Sand\nINTERIOR:Sand\nEXTERIOR:Sand\nSTYLE:modern"
            case LLMClient.ADD_ONS:
                return "Layer 0: symmetric | many\nLayer 1: erratic | many\nLayer 2: symmetric | few\n"
            case _:
                return "Layer 0: Single block"


    async def get_llm_response(self, system_message, prompt, **kwargs):
        raise NotImplementedError("The mock client does not support the get_llm_response method")

