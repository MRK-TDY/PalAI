from datetime import datetime
import tempfile
import colorama
import os
import sys
import shutil

from langchain.memory import ConversationStringBufferMemory

sys.path.append(os.path.dirname(__file__))

from visualizer import ObjVisualizer
from model_capturer import screenshot_model

import base64
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema.messages import HumanMessage, AIMessage

class PalAI():
    def __init__(self, prompts_file, temperature, model_name, image_model_name, api_key, max_tokens, verbose=False):
        self.prompts_file = prompts_file
        self.system_prompt = self.prompts_file['system_prompt']
        self.prompt_template = self.prompts_file['prompt_template']
        self.llm = ChatOpenAI(model=model_name, temperature=temperature, api_key=api_key, max_tokens=max_tokens)
        self.mm_llm = ChatOpenAI(model=image_model_name, temperature=temperature, api_key=api_key,
                                 max_tokens=max_tokens)
        self.verbose = verbose

        os.chdir(os.path.dirname(__file__))

    def get_llm_response(self, system_message, prompt, image_path = ""):
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
                ("user", "{prompt}")
            ])
            llm = self.llm

        self.chain = prompt | llm | StrOutputParser()
        response = self.chain.invoke({"system_message": system_message, "prompt": prompt})

        if self.verbose:
            print(f"{colorama.Fore.CYAN}Response:{colorama.Fore.RESET} {response}")

        return response

    def format_prompt(self, user_prompt):
        return (self.system_prompt, self.prompt_template)

    def build(self, prompt):

        # prompt = self.get_llm_response(self.prompts_file["plan_system_message"],
        #                                self.prompts_file["plan_prompt"].format(prompt))
        visualizer = ObjVisualizer()
        system_message, prompt_template = self.format_prompt(prompt)
        complete_building = []
        temp_files_to_delete = []
        history = []

        try:
            for i in range(3):

                formatted_prompt = prompt_template.format(prompt=prompt, layer=i)
                if len(history) > 0:
                    aux = ""
                    for j, building_layer in enumerate(history):
                        aux += f"Building at layer {j}:\n{building_layer}"
                    formatted_prompt = f"Previous layers:\n{aux}\n\nRequest:{formatted_prompt}"


                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_image, \
                        tempfile.NamedTemporaryFile(delete=False, suffix=".obj") as temp_obj:
                    screenshot_model(obj_path if i > 0 else "", temp_image.name)
                    # shutil.copy2(temp_image.name, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}.png")


                    response = self.get_llm_response(system_message, formatted_prompt, temp_image.name)

                    history.append(response)
                    new_layer = self.extract_building_information(response, i)
                    complete_building.extend(new_layer)
                    obj_content = visualizer.generate_obj(complete_building)

                    temp_obj.write(obj_content.encode())
                    temp_obj.flush()

                    # Remember the paths to delete them later
                    temp_files_to_delete.append(temp_image.name)
                    temp_files_to_delete.append(temp_obj.name)

                    # If you need to use the obj file for the next iteration
                    obj_path = temp_obj.name

            return complete_building
        finally:
            # Cleanup temporary files
            for file_path in temp_files_to_delete:
                os.remove(file_path)

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
            blocks.append({'type': block[0], 'position': f"({position[1]},{level},{position[0]})"})

        return blocks
