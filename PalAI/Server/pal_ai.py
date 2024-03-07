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
        self.system_prompt = self.prompts_file.get('system_prompt', "")
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
        building = []
        temp_files_to_delete = []
        history = []
        plan_list = [i for i in architect_plan.split("\n") if i.lower().startswith(f"layer")]

        obj_path = ""

        try:
            for i, layer_prompt in enumerate(plan_list):
                current_layer_prompt = prompt_template.format(prompt=layer_prompt, layer=i)

                if len(history) > 0:
                    complete_history = ('\n\n').join(history)
                    formatted_prompt = f"Current request: {current_layer_prompt}\n\nHere are the previous layers:\n{complete_history}"
                else:
                    formatted_prompt = current_layer_prompt

                if i == 0:
                    example = self.prompts_file["basic_example"]
                else:
                    example =  self.prompts_file["basic_example"]

                system_message = system_message_template.format(example=example)

                if self.use_images:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_image, \
                            tempfile.NamedTemporaryFile(delete=False, suffix=".obj") as temp_obj:
                        screenshot_model(obj_path, temp_image.name)

                        response = self.get_llm_response(system_message, formatted_prompt, temp_image.name)

                        history.append(f"Layer {i}:")
                        history.append(current_layer_prompt)
                        history.append(self.extract_history(formatted_prompt, response))
                        new_layer = self.extract_building_information(response, i)
                        building.extend(new_layer)
                        obj_content = visualizer.generate_obj(building)

                        temp_obj.write(obj_content.encode())
                        temp_obj.flush()

                        # Remember the paths to delete them later
                        temp_files_to_delete.append(temp_image.name)
                        temp_files_to_delete.append(temp_obj.name)

                        # If you need to use the obj file for the next iteration
                        obj_path = temp_obj.name

                else:
                    response = self.get_llm_response(system_message, formatted_prompt)
                    history.append(f"Layer {i}:")
                    history.append(current_layer_prompt)
                    history.append(self.extract_history(formatted_prompt, response))
                    new_layer = self.extract_building_information(response, i)
                    building.extend(new_layer)

                api_result[f"bricklayer_{i}"] = [l for l in response.split("\n") if l != ""]

            # WINDOW AND DOOR PLACEMENT
            add_on_prompt = self.format_add_on_prompt(plan_list, building)
            building = self.get_llm_response(self.prompts_file["add_on_system_message"], add_on_prompt)
            api_result["add_on_agent"] = [l for l in building.split("\n") if l != ""]
            building = self.extract_building_information(building)

            api_result["result"] = building
            return api_result
        finally:
            # Cleanup temporary files
            for file_path in temp_files_to_delete:
                os.remove(file_path)

    def format_add_on_prompt(self, plan_list, building):
        plan = "\n".join(plan_list)
        building = self.json_to_pal_script(building)
        return f"Here is the requested building:\n{plan}\nAnd here is the building code without doors or windows:\n{building}."

    def json_to_pal_script(self, text):
        pal_script = ""
        for i in text:
            type = i['type']
            position = i['position'].replace("(", "").replace(")","").split(",")

            pal_script += f"B:{type}|{position[2]},{position[0]}|{position[1]}"
            # TODO: add-ons
            pal_script += "\n"
        return pal_script


    def extract_history(self, user_message, response):
        """
        Extracts history from the response.
        Only includes lines that create blocks and doesn't include add-ons to blocks.
        This is because latter layers may not know this part of the syntax
        :param response: LLM response
        :return string: Only relevant history
        """
        aux = "User Request: " + user_message + "\n"
        for line in response.split("\n"):
            if line.startswith("B:"):
                # parts = line.split("|")
                # if len(parts) == 3:
                #     line = "|".join(parts[:-1])
                aux += line + "\n"
        return aux

    def extract_building_information(self, text, level = None):
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
                if level is not None:
                    line += f"|{level}"  #if a level is given then it is not present in the script at this point
                building_info.append(line[2:])

        blocks = []
        for block in building_info:
            block = block.split('|')
            position = block[1].split(',')
            aux = {'type': block[0], 'position': f"({position[1]},{block[2]},{position[0]})"}
            if len(block) == 5:
                position = block[4].split(',')
                aux['tags'] = {"type": block[3].upper(), "position": f"({position[1]},{block[2]},{position[0]})"}
            blocks.append(aux)

        return blocks

