from configparser import RawConfigParser
from loguru import logger
import base64
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema.messages import HumanMessage
from PalAI.Server.LLMClients.llm_client import LLMClient
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
import colorama
import os


class GPTClient(LLMClient):

    def __init__(self, prompts_file, **kwargs):
        LLMClient.__init__(self, prompts_file)

        self.api_key = self.config.get("openai", "api_key")
        self.model_name = self.config.get("openai", "model_name")
        self.verbose = kwargs.get("verbose", False)

        if self.api_key is not None:
            self.llm = ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                api_key=self.api_key,
                max_tokens=self.max_tokens,
            )
        self.price_rate = 0.0000005

        if "gpt4" in self.model_name:
            self.price_rate = 0.00003

    def SetModel(self, model_name):
        self.model_name = model_name

        if "gpt-3" in model_name:
            self.price_rate = 0.0000005
        elif "gpt-4" in self.model_name:
            self.price_rate = 0.00003

        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            api_key=self.api_key,
            max_tokens=self.max_tokens,
        )

    async def get_llm_response(self, system_message, prompt, image_path="", **kwargs):
        if self.verbose:
            logger.info(
                f"{colorama.Fore.GREEN}System message:{colorama.Fore.RESET} {system_message}"
            )
            logger.info(f"{colorama.Fore.BLUE}Prompt:{colorama.Fore.RESET} {prompt}")

        self.prompt_total += system_message + prompt

        chat_prompt = ChatPromptTemplate.from_messages(
            [("system", "{system_message}"), ("user", f"{prompt}")]
        )

        llm = self.llm
        chain = chat_prompt | llm | StrOutputParser()

        # Invoke the chain asynchronously
        try:
            response = await chain.ainvoke(
                {"system_message": system_message, "prompt": chat_prompt}
            )
        except Exception as e:
            logger.error(f"Error during chain invocation: {e}")
            raise

        if self.verbose:
            logger.info(f"{colorama.Fore.CYAN} Response:{colorama.Fore.RESET} {response}")

        return response

    async def get_llm_single_response(
        self, context_type, context_file, original_prompt, debug=False
    ):

        system_message = context_file[context_type + "_system_message"]
        examples = context_file[context_type + "_examples"]
        user = []
        assistant = []
        for key in examples.keys():
            user.append(examples[key]["user"])
            assistant.append(examples[key]["assistant"])

        messages = []
        messages.append(("system", system_message))
        self.prompt_total += system_message

        for i, user_prompt in enumerate(user):
            messages.append(("user", user_prompt))
            messages.append(("assistant", assistant[i]))
            self.prompt_total += user_prompt
            self.prompt_total += assistant[i]

        self.prompt_total += original_prompt

        prompt = ChatPromptTemplate.from_messages(messages)
        llm = self.llm

        self.chain = prompt | llm | StrOutputParser()
        response = await self.chain.ainvoke(
            {
                "system_message": system_message,
                "example": messages,
                "prompt": original_prompt,
            }
        )

        if self.verbose:
            logger.info(f"{colorama.Fore.CYAN}Response:{colorama.Fore.RESET} {response}")

        return response
