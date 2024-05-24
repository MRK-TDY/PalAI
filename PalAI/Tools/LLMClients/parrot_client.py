from PalAI.Server.LLMClients.llm_client import LLMClient

class ParrotClient(LLMClient):
    """ Repeats the prompt as a layer, used to debug the layers that have been implemented"""

    def __init__(self, prompts_file, logger, **kwargs):
        LLMClient.__init__(self, prompts_file, logger)

        # self.model_name = self.config.get('openai', 'model_name')
        self.logger = logger
        self.price_rate = 0

    async def get_agent_response(self, agent, prompt, **kwargs):
        prompt = prompt.replace("\n", " ").replace("USER:", "").replace("ARCHITECT:", "")
        aux = ""
        for i, l in enumerate(prompt.split("\n")):
            if not l.lower().startswith("layer"):
                aux += f"Layer {i}: {l}\n"
            else:
                aux += l + "\n"
        prompt = aux.strip()
        match agent:
            case "architect":
                return f"We will create a building made up of 1 layers.\n{prompt}"
            case "materials":
                return "FLOOR:Sand\nINTERIOR:Sand\nEXTERIOR:Sand\nSTYLE:modern"
            case "add_ons":
                return "Layer 0: symmetric | many\n"
            case _:
                return prompt


    async def get_llm_response(self, system_message, prompt, **kwargs):
        raise NotImplementedError("The mock client does not support the get_llm_response method")

