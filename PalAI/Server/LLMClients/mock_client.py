from PalAI.Server.LLMClients.llm_client import LLMClient

class MockClient(LLMClient):

    def __init__(self, prompts_file, logger, **kwargs):
        LLMClient.__init__(self, prompts_file, logger)

        # self.model_name = self.config.get('openai', 'model_name')
        self.logger = logger
        self.price_rate = 0

    async def get_agent_response(self, agent, prompt, **kwargs):
        match agent:
            case "architect":
                return "Layer 0: Single block"
            case "bricklayer":
                return "B:CUBE|0,0"
            case "materials":
                return "FLOOR:Sand\nINTERIOR:Sand\nEXTERIOR:Sand\nSTYLE:blocky"
            case "add_ons":
                return "B:CUBE|0,0|0|WINDOW|1,0"
            case _:
                return "Layer 0: Single block"


    async def get_llm_response(self, system_message, prompt, **kwargs):
        raise NotImplementedError("The mock client does not support the get_llm_response method")
