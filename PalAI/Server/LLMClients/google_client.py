import os
from PalAI.Server.LLMClients.llm_client import LLMClient
from configparser import RawConfigParser
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema.messages import HumanMessage
import pathlib
import textwrap
from  loguru import logger
import google.generativeai as genai

# Used to securely store your API key


class GoogleClient(LLMClient):

    def __init__(self, prompts_file):
        LLMClient.__init__(self, prompts_file)
        self.api_key = self.config.get("google", "api_key")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-pro")

    async def get_llm_response(self, system_message, prompt, image_path="", **kwargs):

        actual_prompt = self.prompts_file["plan_system_message"]
        actual_prompt += prompt
        logger.info(actual_prompt)

        response = self.model.generate_content(actual_prompt)
        logger.info("Response:" + str(response))

        logger.info(response.text)
        return response.text
