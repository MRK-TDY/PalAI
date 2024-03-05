import tempfile
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

class PalAI():
    def __init__(self, prompts_file, temperature, model_name, image_model_name, api_key, max_tokens, use_images, verbose=False):
        self.prompts_file = prompts_file
        self.system_prompt = self.prompts_file.get('grid_system_prompt', "")
        self.prompt_template = self.prompts_file.get('prompt_template', "")

        if api_key is not None:
            self.llm = ChatOpenAI(model=model_name, temperature=temperature, api_key=api_key, max_tokens=max_tokens)
            self.mm_llm = ChatOpenAI(model=image_model_name, temperature=temperature, api_key=api_key,
                                     max_tokens=max_tokens)

        self.use_images = use_images
        self.verbose = verbose

        os.chdir(os.path.dirname(__file__))

    @classmethod
    def create_default(cls):
        return cls({}, 0.7, 'gpt-4', 'gpt-4-vision-preview', None, 1024, False, True)

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
                ("user", f"{prompt}")
            ])
            llm = self.llm

        self.chain = prompt | llm | StrOutputParser()
        response = self.chain.invoke({"system_message": system_message, "prompt": prompt})

        if self.verbose:
            print(f"{colorama.Fore.CYAN}Response:{colorama.Fore.RESET} {response}")

        return response

    
    def format_prompt(self):
        return (self.system_prompt, self.prompt_template)


    def build(self, architect_plan):

        architect_plan = self.get_llm_response(self.prompts_file["plan_system_message"],
                                               self.prompts_file["plan_prompt"].format(architect_plan))
        api_result = {"architect": [l for l in architect_plan.split("\n") if l != ""]}
        visualizer = ObjVisualizer()
        system_message_template, prompt_template = self.format_prompt()
        complete_building = []
        temp_files_to_delete = []
        history = []
        layers = [i for i in architect_plan.split("\n") if i.lower().startswith(f"layer")] 

        obj_path = ""

        try:
            for i, layer_prompt in enumerate(layers):
                formatted_prompt = prompt_template.format(prompt=layer_prompt, layer=i)

                if len(history) > 0:
                    complete_history = ('\n\n').join(history)
                    formatted_prompt = f"{complete_history}\n\nCurrent request: {formatted_prompt}"

                if i == 0:
                    example = self.prompts_file["door_example"]
                else:
                    example =  self.prompts_file["window_example"]
                system_message = system_message_template.format(example=example)

                if self.use_images:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_image, \
                            tempfile.NamedTemporaryFile(delete=False, suffix=".obj") as temp_obj:
                        screenshot_model(obj_path, temp_image.name)

                        response = self.get_llm_response(system_message, formatted_prompt, temp_image.name)

                        history.append(self.extract_history(formatted_prompt, response))
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

                else:
                    response = self.get_llm_response(system_message, formatted_prompt)
                    history.append(response)
                    new_layer = self.extract_building_information(response, i)
                    complete_building.extend(new_layer)
                api_result[f"bricklayer_{i}"] = [l for l in response.split("\n") if l != ""]    

            api_result["result"] = complete_building
            return api_result
        finally:
            # Cleanup temporary files
            for file_path in temp_files_to_delete:
                os.remove(file_path)


    def extract_history(user_message, response):
        """
        Extracts history from the response.
        Only includes lines that create blocks and doesn't include add-ons to blocks.
        This is because latter layers may not know this part of the syntax
        :param response: LLM response
        :return string: Only relevant history
        """
        aux = "User Request: " + user_message + "\n"
        lines = response.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("LAYER:"):
                # parts = line.split("|")
                # if len(parts) == 3:
                #     line = "|".join(parts[:-1])
                aux += "\n".join(lines[i:i+6])
        return aux


    def extract_building_information(self, text, layer):
        lines = text.split('\n')

        building_info = []
        i = -1
        while i < len(lines) - 1:
            i += 1
            line = lines[i]
            if line.startswith("LAYER"):
                j = 0
                for j in range(1, 10):  #Max grid size
                    if i + j >= len(lines) or lines[i+j].startswith("END"):
                        break

                grid = [[l for l in k.split(" ")] for k in lines[i + 1: i + j]]
                i += j
                for y in range(len(grid)):
                    for x in range(len(grid[y])):
                        if grid[y][x] == '|':
                            if y >= 0 and grid[y - 1][x] == '1':
                                grid[y -1][x] = '2'
                            elif y < len(grid) - 1 and grid[y + 1][x] == '1':
                                grid[y + 1][x] = '2'

                        if grid[y][x] == '-':
                            if x >= 0 and grid[y][x - 1] == '1':
                                grid[y][x - 1] = '2'
                            elif x < len(grid[y]) - 1 and grid[y][x + 1] == '1':
                                grid[y][x + 1] = '2'

                for y in range(len(grid)):
                    for x in range(len(grid[y])):
                        b = grid[y][x]
                        if b == "1":
                            building_info.append({"type": "CUBE", "position": f"({y},{layer},{x})"})
                        if b == "2":
                            tags = ["DOOR"] if layer == 0 else ["WINDOW"]
                            building_info.append({"type": "CUBE", "position": f"({y},{layer},{x})", "tags": tags})

        return building_info
