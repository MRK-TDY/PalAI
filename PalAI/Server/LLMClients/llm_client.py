from abc import abstractmethod
import os
from configparser import RawConfigParser
from loguru import logger
from PalAI.Server.LLMClients.Examples import example_getter


class LLMClient:

    def __init__(self, prompts_file):
        """Abstract class representing a client for any LLM

        :param prompts_file: prompts to be used
        :type prompts_file: dict
        """
        self.prompts_file = prompts_file
        self.system_prompt = self.prompts_file.get("system_prompt", "")
        self.prompt_template = self.prompts_file.get("prompt_template", "")
        self.prompt_total = ""
        self.price_rate = 0.00000015
        os.chdir(os.path.dirname(__file__))

        self.config = RawConfigParser()
        self.config.read("../../../config.ini")
        self.temperature = float(self.config.get("llm", "temperature"))
        self.max_tokens = int(self.config.get("llm", "max_tokens"))
        self.verbose = bool(self.config.get("llm", "verbose"))

    @abstractmethod
    async def get_llm_response(self, system_message, prompt, image_path="", **kwargs):
        pass

    def _get_agent_system_message(self, agent, **kwargs):
        system_message = ""
        match agent:
            case "architect":
                system_message = self.prompts_file["architect"]
                system_message = system_message.format(
                    presets=kwargs.get("presets", "")
                )
            case "bricklayer":
                system_message = self.prompts_file["bricklayer"]
            case "materials":
                system_message = self.prompts_file["materials"]
                materials = kwargs.get("materials", "")
                styles = kwargs.get("styles", "")
                system_message = system_message.format(
                    materials=materials, styles=styles
                )
            case "add_ons":
                system_message = self.prompts_file["windows"]
                styles = kwargs.get("styles", "")
                quantifiers = kwargs.get("quantifiers", "")
                system_message = system_message.format(
                    styles=styles, quantifiers=quantifiers
                )
            case _:
                system_message = self.prompts_file["architect"]
        return system_message

    async def get_agent_response(self, agent, prompt, **kwargs):
        system_message = self._get_agent_system_message(agent, **kwargs)
        messages = self.preparePrompt(prompt, agent=agent)
        kwargs["messages"] = messages
        return await self.get_llm_response(system_message, prompt, **kwargs)

    def preparePrompt(self, prompt, agent='architect'):

        prompt = prompt.replace("USER: ", "")
        prompt = prompt.replace("ARCHITECT:", "")
        prompt = prompt.replace("ASSISTANT:", "")
        prompt = prompt.replace("\n", "")

        if agent == "architect":
            # logger.info("Architect: \n" + prompt)
            messages = example_getter.getArchitectExamples(prompt)
        elif agent == "bricklayer":
            # logger.info("Bricklayer: \n" + prompt)
            messages = example_getter.getBrickExamples(prompt)
        elif agent == "materials":
            # logger.info("Materials: \n" + prompt)
            messages = example_getter.getMaterialExamples(prompt)
        elif agent == "add_ons":
            # logger.info("Addons: \n" + prompt)
            messages = example_getter.getAddOnsExamples(prompt)
        else:
            messages = example_getter.getArchitectExamples(prompt)

        return messages

    def getTotalPromptsUsed(self):
        return self.prompt_total

    # When it is necessary to treat the prompt more carefully. When systems need user -> assistant type of queries


    def SetModel(self, model_name):
        self.model_name = model_name

        if "13b" in model_name:
            self.price_rate = 0.00000025
        else:
            self.price_rate = 0.00000015
