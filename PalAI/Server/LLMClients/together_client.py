import together
import os
from PalAI.Server.LLMClients.llm_client import LLMClient
from configparser import RawConfigParser
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema.messages import HumanMessage


class TogetherClient(LLMClient):

    def __init__(self, prompts_file):
        super().__init__(self, prompts_file)
        self.api_key = self.config.get('together', 'api_key')
        self.together.api_key = api_key


    async def get_llm_response(self, system_message, prompt, image_path=""):
          prompt = self.prompts_file["plan_system_message"]
          prompt += self.prompts_file["plan_prompt"]
          print("Prompt: \n" + prompt)
          output = together.Complete.create(
          prompt=prompt,
          model=self.model_name,
          max_tokens =self.max_tokens,
          temperature = self.temperature,
          )

          # parse the completion then print the whole output
          generatedText = output['output']['choices'][0]['text']
          print(output)
          print("Generated Text:" + generatedText)
          return generatedText
