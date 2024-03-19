from configparser import RawConfigParser
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema.messages import HumanMessage
from PalAI.Server.LLMClients.llm_client import LLMClient
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
import colorama
import os

class GPTClient(LLMClient):

    def __init__(self, prompts_file):
        LLMClient.__init__(self, prompts_file)

        self.api_key = self.config.get('openai', 'api_key')
        self.model_name = self.config.get('openai', 'model_name')

        if self.api_key is not None:
            self.llm = ChatOpenAI(model=self.model_name, temperature=self.temperature, api_key=self.api_key, max_tokens=self.max_tokens)



    async def get_llm_response(self, system_message, prompt, image_path = ""):
        if self.verbose:
            print(f"{colorama.Fore.GREEN}System message:{colorama.Fore.RESET} {system_message}")
            print(f"{colorama.Fore.BLUE}Prompt:{colorama.Fore.RESET} {prompt}")

        if image_path != "":
            with open(image_path, "rb") as image_file:
                image = base64.b64encode(image_file.read()).decode('utf-8')

            prompt = ChatPromptTemplate.from_messages([
                ("system", "{system_message}"),
                HumanMessage(content=[
                    {"type": "text", "text": f"{prompt}"},
                    {"type": "image_url",
                     "image_url": f"data:image/jpeg;base64,{image}"}
                ])
            ])
            llm = self.mm_llm

        else:
            prompt = ChatPromptTemplate.from_messages( [
                ("system", "{system_message}"),
                ("user", f"{prompt}")
            ])
            llm = self.llm

        self.prompt_total += system_message
        self.prompt_total += prompt

        self.chain = prompt | llm | StrOutputParser()
        response = await self.chain.ainvoke({"system_message": system_message, "prompt": prompt})

        if self.verbose:
            print(f"{colorama.Fore.CYAN}Response:{colorama.Fore.RESET} {response}")

        return response