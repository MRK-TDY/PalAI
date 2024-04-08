import json
import os

from colorama import Fore
import colorama

from PalAI.Server.LLMClients import gpt_client, together_client, google_client, anyscale_client, local_client
from PalAI.Server.post_process import PostProcess
from PalAI.Server.decorator import Decorator

class PalAI():

    def __init__(self, prompts_file, llm=None, web_socket = None):
        colorama.init(autoreset=True)

        self.material_types = ["Generic White",
                 "Plastic Orange",
                 "Concrete White",
                 "Metal Blue",
                 "Metal Dark Blue",
                 "Honeycomb White",
                 "Grey Light Wood",
                 "Concrete Grey",
                 "Concrete Dark Stripes Blue",
                 "Marble",
                 "Dark Marble",
                 "Sand",
                 "Dark Red",
                 "Molten Marble",
                 "Plastic Red",
                 "Stone Light Grey",
                 "Dark Concrete"]


        if llm is not None and isinstance(llm, str):
            match llm:
                case 'gpt':
                    self.llm_client = gpt_client.GPTClient(prompts_file)
                case 'together':
                    self.llm_client = together_client.TogetherClient(prompts_file)
                case 'google':
                    self.llm_client = google_client.GoogleClient(prompts_file)
                case 'anyscale':
                    self.llm_client = anyscale_client.AnyscaleClient(prompts_file)
                case 'local':
                    self.llm_client = local_client.LocalClient(prompts_file, verbose = True)
        elif llm is not None:
            self.llm_client = llm

        self.building = []
        self.history = []
        self.api_result = {}

        self.post_process = PostProcess()

        self.ws = web_socket
        self.prompts_file = prompts_file
        self.system_prompt = self.prompts_file.get('system_prompt', "")
        self.prompt_template = self.prompts_file.get('prompt_template', "")

        os.chdir(os.path.dirname(__file__))


    async def build(self, prompt, ws = None):
        self.prompt = prompt
        self.original_prompt = prompt
        if ws is not None:
            self.ws = ws

        print(f"{Fore.BLUE}Received prompt{Fore.RESET}: {prompt}")

        #TODO: do requests that may be parallel in parallel

        await self.get_architect_plan()
        print(f"{Fore.BLUE}Received architect plan {self.plan_list}" )

        await self.build_structure()
        print(f"{Fore.BLUE}Received basic structure")

        await self.apply_add_ons()
        print(f"{Fore.BLUE}Received add-ons")

        await self.get_artist_response()
        print(f"{Fore.BLUE}Received artist response")

        await self.apply_style()
        print(f"{Fore.BLUE}Applied style {self.style}")

        await self.decorate()

        self.api_result["result"] = self.building
        return self.api_result


    async def get_architect_plan(self):
        self.prompt = await self.llm_client.get_llm_response(self.prompts_file["plan_system_message"],
                                                                self.prompts_file["plan_prompt"].format(self.prompt), type='architect')
        self.api_result["architect"] = [l for l in self.prompt.split("\n") if l != ""]
        self.plan_list = [i for i in self.prompt.split("\n") if i.lower().startswith(f"layer") or i.lower().startswith(f" layer") or i.lower().startswith(f"  layer")]

    async def build_structure(self):
            for i, layer_prompt in enumerate(self.plan_list):
                current_layer_prompt = self.prompt_template.format(prompt=layer_prompt, layer=i)

                #if len(self.history) > 0:
                #    complete_history = ('\n\n').join(self.history)
                #    formatted_prompt = f"Current request: {current_layer_prompt}\n\nHere are the previous layers:\n{complete_history}"
                #else:
                formatted_prompt = current_layer_prompt

                if i == 0:
                    example = self.prompts_file["basic_example"]
                else:
                    example =  self.prompts_file["basic_example"]

                system_message = self.system_prompt.format(example=example)
                response = await self.llm_client.get_llm_response(system_message, formatted_prompt, type='bricklayer')
                self.history.append(f"Layer {i}:")
                self.history.append(current_layer_prompt)
                self.history.append(self.extract_history(formatted_prompt, response))
                new_layer = self.extract_building_information(response, i)
                self.building.extend(new_layer)

                if self.ws is not None:
                    message = {"value": new_layer}
                    message["event"] = "layer"
                    self.ws.send(json.dumps(message))
                self.api_result[f"bricklayer_{i}"] = [l for l in response.split("\n") if l != ""]

                print(f"{Fore.GREEN}Received layer {i} of structure")


    async def apply_add_ons(self):
        plan = "\n".join(self.plan_list)
        building = self.json_to_pal_script(self.building)
        add_on_prompt = f"Here is the requested building:\n{plan}\nAnd here is the building code without doors or windows:\n{building}."
        add_ons = await self.llm_client.get_llm_response(self.prompts_file["add_on_system_message"], add_on_prompt, type="addons")
        add_ons = self.extract_building_information(add_ons)
        self.building = self.overlap_blocks(self.building, add_ons)
        self.api_result["add_on_agent"] = self.building

        if self.ws is not None:
            message = {"value": self.building}
            message["event"] = "add_ons"
            self.ws.send(json.dumps(message))


    async def get_artist_response(self):
        materials_response = await self.llm_client.get_llm_response(
                self.prompts_file["material_system_message"].format(materials= self.material_types,
                                                                    styles = self.post_process.get_available_styles()),
                self.original_prompt, type='materials')
        material = {}
        for l in materials_response.split("\n"):
            l = l.upper().split(":")
            print("HERE IS L: " + str(l))
            if len(l) == 2:
                if "STYLE" in l[0]:
                    self.style = l[1].lower().strip()
                    material["STYLE"] = l[1].strip()
                elif "FLOOR" in l[0]:
                    material["FLOOR"] = l[1].strip()
                elif "INTERIOR" in l[0]:
                    material["INTERIOR"] = l[1].strip()
                elif "EXTERIOR" in l[0]:
                    material["EXTERIOR"] = l[1].strip()

        self.api_result["materials"] = material
        if self.ws is not None:
            print("WS Material: " + str(material))
            message = {"value": material}
            message["event"] = "material"
            self.ws.send(json.dumps(message))


    async def apply_style(self):
        try:
            self.post_process.import_building(self.building)
            self.building = self.post_process.style(self.style)
        except:
            self.style = "no style"
            print("Style Error")
            self.ws.send(json.dumps("Error found with post-processing"))


    async def decorate(self):
        decorator = Decorator()
        decorator.import_building(self.building)
        self.decorations = decorator.decorate()

        self.api_result["decorations"] = self.decorations

        if self.ws is not None:
            message = {"value": self.decorations}
            message["event"] = "decorations"
            self.ws.send(json.dumps(message))

    def json_to_pal_script(self, building):
        """
        Converts a building from JSON to be used to communicate with the LLM
        :returns : (str) same building in the format that LLM's consume
        :param building: json formatted building
        """
        pal_script = ""
        for i in building:
            type = i['type']
            position = i['position'].replace("(", "").replace(")","").split(",")

            pal_script += f"B:{type}|{position[2]},{position[0]}|{position[1]}"
            pal_script += "\n"
        return pal_script

    def overlap_blocks(self, base_structure, extra_blocks):
        """
        Overlaps a base structure with a set of extra blocks
        Returns a structure containing all blocks of both sets, prioritizing the first argument
        :param base_structure: set of blocks with priority
        :param extra_blocks: set of blocks with no priority
        """
        for b in extra_blocks:
            if any([x for x in base_structure if x["position"] == b["position"]]):
                   base_structure.append(b)
        return base_structure

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
            try:
                block = block.split('|')
                position = block[1].split(',')
                aux = {'type': block[0], 'position': f"({position[1]},{block[2]},{position[0]})"}
                if len(block) == 5:
                    position = block[4].split(',')
                    aux['tags'] = {"type": block[3].upper(), "position": f"({position[1]},{block[2]},{position[0]})"}
                blocks.append(aux)
            except:
                continue
        return blocks

    def extract_materials(self, material_response):
        materials = {}
        for line in material_response.split("\n"):
            if ": " in line:
                parts = line.upper().split(": ")
                if parts[0] in ["FLOOR", "INTERIOR", "EXTERIOR"]:
                    # TODO: should we verify if material is on list?
                    materials[parts[0]] = parts[1]

        return materials

