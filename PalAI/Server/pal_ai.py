import json
import os

from colorama import Fore
import Levenshtein
import logging

from PalAI.Server.LLMClients import (
    gpt_client,
    together_client,
    google_client,
    anyscale_client,
    local_client,
)
from PalAI.Server.post_process import PostProcess
from PalAI.Server.decorator import Decorator


class PalAI:

    def __init__(self, prompts_file, llm, logger=None, web_socket=None):
        """

        :param prompts_file: all prompts to be used
        :type prompts_file: dict
        :param llm: llm client to be used or type of client (gpt, together, google, anyscale, local)
        :type llm: str or LLMClient
        :param web_socket: web socket to send messages to
        :type web_socket: web_socket
        """

        self.material_types = [
            "Generic White",
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
            "Dark Concrete",
        ]

        if logger is not None:
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter('%(levelname)s - %(message)s')
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

        if llm is not None and isinstance(llm, str):
            match llm:
                case "gpt":
                    self.llm_client = gpt_client.GPTClient(
                        prompts_file, logger=self.logger
                    )
                case "together":
                    self.llm_client = together_client.TogetherClient(
                        prompts_file, logger=self.logger
                    )
                case "google":
                    self.llm_client = google_client.GoogleClient(
                        prompts_file, logger=self.logger
                    )
                case "anyscale":
                    self.llm_client = anyscale_client.AnyscaleClient(
                        prompts_file, logger=self.logger
                    )
                case "local":
                    self.llm_client = local_client.LocalClient(
                        prompts_file, verbose=True, logger=self.logger
                    )
        elif llm is not None:
            self.llm_client = llm

        self.building = []
        self.history = []
        self.api_result = {}

        self.post_process = PostProcess()

        self.ws = web_socket
        self.prompts_file = prompts_file
        self.system_prompt = self.prompts_file.get("system_prompt", "")
        if type(llm) == local_client.LocalClient:
            self.prompt_template = self.prompts_file.get("prompt_local_template", "")
        else:
            self.prompt_template = self.prompts_file.get("prompt_template", "")

        os.chdir(os.path.dirname(__file__))

    async def build(self, prompt, ws=None):
        """Constructs the entire building based on the prompt

        :type prompt: string
        :param ws: web socket to send messages to
        :type ws: web_socket
        :return: complete building
        :rtype: list(dict)
        """
        self.prompt = prompt
        self.original_prompt = prompt
        if ws is not None:
            self.ws = ws

        self.logger.info(f"{Fore.BLUE}Received prompt: {prompt}{Fore.RESET}")

        # TODO: do requests that may be parallel in parallel

        await self.get_architect_plan()
        self.logger.info(f"{Fore.BLUE}Received architect plan {self.plan_list}{Fore.RESET}")

        await self.build_structure()
        self.logger.info(f"{Fore.BLUE}Received basic structure{Fore.RESET}")

        await self.apply_add_ons()
        self.logger.info(f"{Fore.BLUE}Received add-ons{Fore.RESET}")

        await self.get_artist_response()
        self.logger.info(f"{Fore.BLUE}Received artist response{Fore.RESET}")

        await self.apply_style()
        self.logger.info(f"{Fore.BLUE}Applied style {self.style}{Fore.RESET}")

        await self.decorate()
        self.logger.info(f"{Fore.BLUE}Obtained decorations{Fore.RESET}")

        self.api_result["result"] = self.building
        self.logger.info(f"{Fore.GREEN}Finished Request{Fore.RESET}")
        return self.api_result

    async def get_architect_plan(self):
        """Gets the architect's plan for the building"""
        self.prompt = await self.llm_client.get_agent_response(
            "architect", self.prompts_file["plan_prompt"].format(self.prompt)
        )
        self.api_result["architect"] = [l for l in self.prompt.split("\n") if l != ""]
        self.plan_list = [
            i
            for i in self.prompt.split("\n")
            if i.lstrip().lower().startswith(f"layer")
        ]

    async def build_structure(self):
        """Adds the blocks of the structure, layer by layer and using only cubes for now"""
        for i, layer_prompt in enumerate(self.plan_list):
            current_layer_prompt = self.prompt_template.format(
                prompt=layer_prompt, layer=i
            )

            if len(self.history) > 0:
                complete_history = ('\n').join(self.history)
                formatted_prompt = f"Current request: {current_layer_prompt}\n\nHere are the previous layers:\n{complete_history}"
            else:
                formatted_prompt = current_layer_prompt

            # if i == 0:
            #     example = self.prompts_file["basic_example"]
            # else:
            #     example = self.prompts_file["basic_example"]

            response = await self.llm_client.get_agent_response(
                "bricklayer", formatted_prompt
            )
            self.history.append(f"Layer {i}:")
            self.history.append(current_layer_prompt)
            self.history.append(self.extract_history(formatted_prompt, response))
            new_layer = self.extract_building_information(response, i)
            self.building.extend(new_layer)

            if self.ws is not None:
                message = {"value": new_layer}
                message["event"] = "layer"
                self.ws.send(json.dumps(message))
            self.api_result[f"bricklayer_{i}"] = [
                l for l in response.split("\n") if l != ""
            ]

            self.logger.info(f"{Fore.BLUE}Received layer {i} of structure{Fore.RESET}")

    async def apply_add_ons(self):
        def json_to_pal_script(building):
            """
            Converts a building from JSON to be used to communicate with the LLM
            :param building: json formatted building
            :returns : (str) same building in the format that LLM's consume
            """
            pal_script = ""
            for i in building:
                type = i["type"]
                position = i["position"].replace("(", "").replace(")", "").split(",")

                pal_script += f"B:{type}|{position[2]},{position[0]}|{position[1]}\n"
            return pal_script

        """Adds doors and windows to the building"""
        plan = "\n".join(self.plan_list)
        building = json_to_pal_script(self.building)
        add_on_prompt = f"Here is the requested building:\n{plan}\nAnd here is the building code without doors or windows:\n{building}. Please add windows and doors where you see fit \n"
        self.logger.debug(f"ADDON PROMPT: {add_on_prompt}")
        add_ons = await self.llm_client.get_agent_response("add_ons", add_on_prompt)
        add_ons = self.extract_building_information(add_ons)
        self.building = self.overlap_blocks(self.building, add_ons)
        self.api_result["add_on_agent"] = self.building

        if self.ws is not None:
            message = {"value": self.building}
            message["event"] = "add_ons"
            self.ws.send(json.dumps(message))

    async def get_artist_response(self):
        materials_response = await self.llm_client.get_agent_response(
            "materials",
            self.original_prompt,
            materials=self.material_types,
            styles=self.post_process.get_available_styles(),
        )

        material = {}
        for l in materials_response.split("\n"):
            l = [i.strip() for i in l.upper().split(":")]
            if len(l) == 2:
                if "STYLE" in l[0]:
                    self.style = self._get_similarity_response(l[1].strip(), self.post_process.get_styles_list())
                    material["STYLE"] = self.style
                elif "FLOOR" in l[0]:
                    material["FLOOR"] = self._get_similarity_response(l[1].strip(), self.material_types)
                elif "INTERIOR" in l[0]:
                    material["INTERIOR"] = self._get_similarity_response(l[1].strip(), self.material_types)
                elif "EXTERIOR" in l[0]:
                    material["EXTERIOR"] = self._get_similarity_response(l[1].strip(), self.material_types)

        self.api_result["materials"] = material
        if self.ws is not None:
            message = {"value": material}
            message["event"] = "material"
            self.ws.send(json.dumps(message))

    def _get_similarity_response(self, response, possibilities):
        """Takes in a response and a list of possibilities and returns the most similar possibility

        :param response: unsanitized text
        :type response: str
        :param possibilities: list of possibilities
        :type possibilities: list(str)
        """
        aux = sorted(possibilities, key = lambda x: Levenshtein.distance(x, response))
        return aux[0]

    async def apply_style(self):
        """Applies the style received from the artist"""
        try:
            self.post_process.import_building(self.building)
            self.building = self.post_process.style(self.style)
        except Exception as e:
            self.style = "no style"
            self.logger.warning(f"{Fore.RED}Style Error {e}{Fore.RESET}")
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


    def overlap_blocks(self, base_structure, extra_blocks):
        """Overlaps a base structure with a set of extra blocks
        If there are multiple blocks in the same position, the one in the base structure is kept

        :param base_structure: set of blocks with priority
        :type base_structure: list(dict)
        :param extra_blocks: set of blocks with no priority
        :type extra_blocks: list(dict)
        :return: structure containing all blocks of both sets, prioritizing the first argument
        :rtype: list(dict)
        """
        for b in extra_blocks:
            if any([x for x in base_structure if x["position"] == b["position"]]):
                base_structure.append(b)
        return base_structure

    def extract_history(self, user_message, response):
        """Extracts history from the response.
        Only includes lines that create blocks and doesn't include add-ons to blocks.
        This is because latter layers may not know this part of the syntax

        :param response: LLM response
        :type response: str
        :return: Only relevant history
        :rtype: str
        """
        aux = "User Request: " + user_message + "\n"
        for line in response.split("\n"):
            if line.startswith("B:"):
                # parts = line.split("|")
                # if len(parts) == 3:
                #     line = "|".join(parts[:-1])
                aux += line + "\n"
        return aux

    def extract_building_information(self, text, level=None):
        """Extracts building information from the API response.

        :param text: LLM response
        :type text: str
        :return list: List of dictionaries, where each dictionary represents a block.
        :rtype: list(dict)
        """
        lines = text.split("\n")
        building_info = []

        # match lines that have two `|` characters
        for line in lines:
            if line.startswith("B:"):
                try:
                    if level is not None:
                        line += f"|{level}"  # if a level is given then it is not present in the script at this point
                    building_info.append(line[2:])
                except:
                    self.logger.warning(
                        f"{Fore.RED}Error extracting building information from LLM response.{Fore.RESET}"
                    )

        blocks = []
        for block in building_info:
            try:
                block = block.split("|")
                position = block[1].split(",")
                aux = {
                    "type": block[0],
                    "position": f"({position[1]},{block[2]},{position[0]})",
                }
                if len(block) == 5:
                    position = block[4].split(",")
                    aux["tags"] = {
                        "type": block[3].upper(),
                        "position": f"({position[1]},{block[2]},{position[0]})",
                    }
                blocks.append(aux)
            except:
                self.logger.warning(
                    f"{Fore.RED}Error extracting building information from LLM response.{Fore.RESET}"
                )
                continue
        return blocks
