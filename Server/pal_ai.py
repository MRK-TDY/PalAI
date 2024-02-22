import yaml
import colorama
import os
import sys

sys.path.append(os.path.dirname(__file__))

from visualizer import ObjVisualizer
from model_capturer import screenshot_model

import base64
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema.messages import HumanMessage

# https://docs.gpt4all.io/gpt4all_python.html
# https://github.com/nomic-ai/gpt4all

class PalAI():
    def __init__(self, prompts_file, temperature, model_name, image_model_name, api_key, max_tokens, verbose=False):
        self.prompts_file = prompts_file
        self.system_prompt = self.prompts_file['system_prompt']
        self.prompt_template = self.prompts_file['prompt_template']
        self.llm = ChatOpenAI(model=model_name, temperature = temperature, api_key = api_key, max_tokens=max_tokens)
        self.mm_llm = ChatOpenAI(model=image_model_name, temperature = temperature, api_key = api_key, max_tokens=max_tokens)
        self.verbose = verbose

        os.chdir(os.path.dirname(__file__))

    def get_llm_response(self, system_message, prompt, image_path = ""):
        if self.verbose:
            print(f"System message: {system_message}")
            print(f"Prompt: {prompt}")

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
                ("user", "{prompt}")
            ])
            llm = self.llm


        self.chain = prompt | llm | StrOutputParser()
        response = self.chain.invoke({"system_message": system_message, "prompt": prompt})

        if self.verbose:
            print(f"Response: {response}")

        return response

    def format_prompt(self, user_prompt):
        return (self.system_prompt, self.prompt_template.format(user_prompt))

    def build(self, prompt):

        visualizer = ObjVisualizer()
        system_message, formatted_prompt = self.format_prompt(prompt)
        complete_building = []
        for i in range(3):
            image_path = f"temp{i}.png"
            obj_path = f"temp{i - 1}.obj"
            screenshot_model(obj_path, image_path)
            response = self.get_llm_response(system_message, formatted_prompt, image_path)
            new_layer = self.extract_building_information(response, i)
            complete_building.extend(new_layer)
            obj_content = visualizer.generate_obj(complete_building)

            with open(f'temp{i}.obj', 'w') as fptr:
                fptr.write(obj_content)
                fptr.flush()

        return complete_building


    # def extract_building_information(self, text, level):
    #     lines = text.split('\n')
    #
    #     building_info = []
    #     i = 0
    #     while i < len(lines):
    #         line = lines[i]
    #         if line.startswith("LEVEL"):
    #             i += 1
    #             for j in range(0, 5):
    #                 for k, b in enumerate(lines[i+j].split(" ")):
    #                     if b != "0":
    #                         building_info.append({"type": "CUBE", "position": f"({j},{level},{k})"})
    #             level += 1
    #             i += 5
    #         else:
    #             i += 1
    #
    #     return building_info


    def extract_building_information(self, text, level):
        """
        Extracts building information from the API response.
        :param text: API response
        :return list: List of dictionaries, where each dictionary represents a block.
        """
        lines = text.split('\n')
        building_info = []

        # match lines that have two `|` characters
        for line in lines:
            if line.startswith('B:'):
                building_info.append(line[2:])

        blocks = []
        for block in building_info:
            block = block.split('|')
            position = block[1].split(',')
            blocks.append({'type': block[0], 'position': f"({position[0]},{level},{position[1]})"})

        return blocks
