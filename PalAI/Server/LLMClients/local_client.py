from configparser import RawConfigParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from langchain_community.chat_models.huggingface import ChatHuggingFace
from langchain.schema.messages import HumanMessage
from PalAI.Server.LLMClients.llm_client import LLMClient
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from langchain_core.output_parsers import StrOutputParser
import torch
import colorama
import os
import yaml

class LocalClient(LLMClient):

    def __init__(self, prompts_file, **kwargs):
        LLMClient.__init__(self, prompts_file)

        self.model_name = self.config.get('openai', 'model_name')
        self.verbose = kwargs.get('verbose', False)
        # self.device = kwargs.get('device', 'cuda')
        self.model_name = kwargs.get('model_name', 'mistralai/Mistral-7B-Instruct-v0.2')
        model = AutoModelForCausalLM.from_pretrained(self.model_name, device_map='cuda', torch_dtype = torch.bfloat16)
        tokenizer = AutoTokenizer.from_pretrained(self.model_name)

        pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, device_map = 'cuda', torch_dtype=torch.bfloat16, max_new_tokens=500)
        self.hf = HuggingFacePipeline(pipeline=pipe)
        self.price_rate = 0


    async def get_llm_response(self, system_message, prompt):
        if self.verbose:
            print(f"{colorama.Fore.GREEN}System message:{colorama.Fore.RESET} {system_message}")
            print(f"{colorama.Fore.BLUE}Prompt:{colorama.Fore.RESET} {prompt}")

        self.prompt_total += system_message
        self.prompt_total += prompt

        system_message = f"<s>[INST]{system_message}[/INST]</s>"
        prompt = f"[INST]{prompt}[/INST]"
        length = len(prompt) + len(system_message)
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("user", prompt)
        ])
        llm = self.hf

        self.chain = prompt | llm | StrOutputParser()
        response = (await self.chain.ainvoke({"system_message": system_message, "prompt": prompt}))[length:]

        if self.verbose:
            print(f"{colorama.Fore.CYAN}Response:{colorama.Fore.RESET} {response}")

        return response

    async def get_llm_single_response(self, context_type,context_file, original_prompt, debug=False):

        system_message = context_file[context_type + "_system_message"]
        examples =context_file[context_type + "_examples"]
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
        response = await self.chain.ainvoke({"system_message": system_message, "example": messages, "prompt": original_prompt})

        if self.verbose:
            print(f"{colorama.Fore.CYAN}Response:{colorama.Fore.RESET} {response}")

        return response


if __name__ == "main":
    with open(os.path.join(os.path.dirname(__file__), '../../../../prompts.yaml'), 'r') as file:
        prompts_file = yaml.safe_load(file)
    example = prompts_file["basic_example"]
    system = prompts_file.get('system_prompt', "").format(example=example)

    prompt = "I want a tiny house"

    client = LocalClient(prompts_file, verbose = True)
    print(client.get_llm_response(system, prompt))
