import together
import os
from PalAI.Server.LLMClients.llm_client import LLMClient
from configparser import RawConfigParser
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema.messages import HumanMessage


# Pricing https://api.together.xyz/models
class TogetherClient(LLMClient):

    def __init__(self, prompts_file, logger):
        LLMClient.__init__(self, prompts_file, logger)
        self.logger = logger
        self.api_key = self.config.get("together", "api_key")
        self.model_name = self.config.get("together", "model_name")
        self.max_tokens = int(self.config.get("together", "together_max_tokens"))
        self.temperature = float(self.config.get("together", "together_temperature"))
        together.api_key = self.api_key

    async def get_llm_response(self, system_message, prompt, image_path="", **kwargs):

        actual_prompt = self.prompts_file["plan_system_message"]
        actual_prompt += prompt
        self.logger.info(actual_prompt)
        output = together.Complete.create(
            prompt=actual_prompt,
            model=self.model_name,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )

        self.prompt_total += actual_prompt
        # parse the completion then print the whole output
        generatedText = output["output"]["choices"][0]["text"]
        self.logger.info(output)
        self.logger.info("Generated Text:" + generatedText)
        return generatedText
