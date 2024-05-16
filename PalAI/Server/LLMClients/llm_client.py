from abc import abstractmethod
import os
from configparser import RawConfigParser
import logging


class LLMClient:

    def __init__(self, prompts_file, logger):
        """Abstract class representing a client for any LLM

        :param prompts_file: prompts to be used
        :type prompts_file: dict
        """
        self.logger = logger
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

        return await self.get_llm_response(system_message, prompt, **kwargs)

    def getTotalPromptsUsed(self):
        return self.prompt_total

    # When it is necessary to treat the prompt more carefully. When systems need user -> assistant type of queries
    def preparePrompt(self, system_message):
        prompt_array = system_message.split("\n")
        user = []
        assistant = [""]
        instructions = ""
        assistant_index = 0
        bUser = False
        bAssistant = False
        for p in prompt_array:
            if len(p) < 2:
                continue
            if "EXAMPLE" in p:
                continue
            if "USER" in p:
                bUser = True
                bAssistant = False
            if "ARCHITECT" in p:
                bAssistant = True
                bUser = False
                assistant_index += 1

            if bUser:
                user.append(p)

            elif bAssistant:
                if len(assistant) <= assistant_index:
                    assistant.append(p)
                else:
                    assistant[assistant_index] += p

            else:
                instructions += p

        return user, assistant, instructions

    def SetModel(self, model_name):
        self.model_name = model_name

        if "13b" in model_name:
            self.price_rate = 0.00000025
        else:
            self.price_rate = 0.00000015
