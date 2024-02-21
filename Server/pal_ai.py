import yaml
import colorama
import os

from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# https://docs.gpt4all.io/gpt4all_python.html
# https://github.com/nomic-ai/gpt4all

class PalAI():
    def __init__(self, prompts_file, temperature, model_name, api_key, max_tokens, verbose=False):
        self.prompts_file = prompts_file
        self.system_prompt = self.prompts_file['system_prompt']
        self.prompt_template = self.prompts_file['prompt_template']
        llm = ChatOpenAI(model=model_name, temperature = temperature, api_key = api_key, max_tokens=max_tokens)
        prompt = ChatPromptTemplate.from_messages( [
            ("system", "{system_message}"),
            ("user", "{prompt}")
        ])
        self.chain = prompt | llm | StrOutputParser()
        self.verbose = verbose

    def get_llm_response(self, system_message, prompt):
        if self.verbose:
            print(f"System message: {system_message}")
            print(f"Prompt: {prompt}")

        response = self.chain.invoke({"system_message": system_message, "prompt": prompt})

        if self.verbose:
            print(f"Response: {response}")

        return response

    def format_prompt(self, user_prompt):
        return (self.system_prompt, self.prompt_template.format(user_prompt))

    def extract_building_information(self, text):
        lines = text.split('\n')

        building_info = []
        i = 0
        level = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith("LEVEL"):
                i += 1
                for j in range(0, 5):
                    for k, b in enumerate(lines[i+j].split(" ")):
                        if b != "0":
                            building_info.append({"type": "CUBE", "position": f"({j},{level},{k})"})
                level += 1
                i += 5
            else:
                i += 1

        return building_info


    # def extract_building_information(self, text):
    #     """
    #     Extracts building information from the API response.
    #     :param text: API response
    #     :return list: List of dictionaries, where each dictionary represents a block.
    #     """
    #     lines = text.split('\n')
    #     building_info = []
    #
    #     # match lines that have two `|` characters
    #     for line in lines:
    #         if line.startswith('B:'):
    #             building_info.append(line[2:])
    #
    #     blocks = []
    #     for block in building_info:
    #         block = block.split('|')
    #         blocks.append({'type': block[0], 'position': f"({block[1]})"})
    #
    #     return blocks