import json
import os
import random
from configparser import RawConfigParser
from dataclasses import dataclass

import Levenshtein
import sentry_sdk
from colorama import Fore
from loguru import logger

import PalAI.Server.door_layer as door_layer
import PalAI.Server.gardener as gardener
import PalAI.Server.window_layer as window_layer
from PalAI.Server.decorator import Decorator
from PalAI.Server.LLMClients import gpt_client
from PalAI.Server.LLMClients.llm_client import LLMClient
from PalAI.Server.placeable import Placeable
from PalAI.Server.post_process import PostProcess
from PalAI.Server.utils import log_additional_data


class PalAI:
    ARCHITECT = "architect"
    ARTIST = "artist"
    DECORATOR = "decorator"
    ADD_ONS = "add_ons"
    GARDEN = "garden"

    @dataclass
    class PalAIRequest:
        create_windows: bool
        create_materials: bool
        create_garden: bool
        create_doors: bool
        apply_post_process: bool
        create_decorations: bool

        @staticmethod
        def full_request():
            return PalAI.PalAIRequest(True, True, True, True, True, True)

        @staticmethod
        def layers_only():
            return PalAI.PalAIRequest(False, False, False, False, False, False)

    def __init__(self, prompts_file, llm, web_socket=None, rng=None):
        """
        :param prompts_file: all prompts to be used
        :type prompts_file: dict
        :param llm: llm client to be used or type of client (gpt, together, google, anyscale, local)
        :type llm: str or LLMClient
        :param web_socket: web socket to send messages to
        :type web_socket: web_socket
        """

        materials = [
            "GENERIC WHITE",
            "PLASTIC ORANGE",
            "CONCRETE WHITE",
            "HONEYCOMB BLUE",
            "METAL",
            "HONEYCOMB WHITE",
            "HONEYCOMB YELLOW",
            "GREY LIGHT WOOD",
            "CONCRETE GREY",
            "CONCRETE DARK STRIPES BLUE",
            "MARBLE",
            "DARK MARBLE",
            "SAND",
            "DARK RED",
            "MOLTEN MARBLE",
            "PLASTIC RED",
            "STONE LIGHT GREY",
            "DARK CONCRETE",
            "DARK PATTERN",
            "WORN DOWN ORANGE",
            "WORN DOWN PINK",
            "WORN DOWN RED",
            "WORN DOWN GREEN",
            "WORN DOWN BLUE",
            "WORN DOWN BROWN",
            "WORN DOWN WOOD",
            "LIGHT WOOD",
            "HONEYCOMB STEEL",
            "HONEYCOMB DARK GREY",
        ]
        self.material_types = {"floor": materials, "interior": materials, "exterior": materials}

        if llm is not None and isinstance(llm, str):
            self.llm_client = gpt_client.GPTClient(prompts_file)

        elif llm is not None:
            self.llm_client = llm

        with open(os.path.join(os.path.dirname(__file__), "layers.json"), "r") as file:
            self.layers = json.load(file)["layers"]

        with open(os.path.join(os.path.dirname(__file__), "windows.json"), "r") as file:
            self.windows = json.load(file)
        self.building: list[Placeable] = []
        self.history = []
        self.api_result = {}

        if rng is None:
            self.rng = random.Random()
        else:
            self.rng = rng
        self.post_process = PostProcess()

        config_path = os.getenv("CONFIG_PATH", "config.ini")
        self.config = RawConfigParser()
        self.config.read(
            os.path.join(os.path.dirname(__file__), "../../" + config_path)
        )

        self.ws = web_socket
        self.prompts_file = prompts_file
        self.system_prompt = self.prompts_file.get("system_prompt", "")
        self.prompt_template = self.prompts_file.get("prompt_template", "")

        os.chdir(os.path.dirname(__file__))

    @sentry_sdk.trace
    async def build(
        self,
        prompt,
        materials: dict[str, list[str]] = None,
        decorations: list[str] = None,
        ws=None,
        manager=None,
        request_type: PalAIRequest = None,
    ):
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
        if manager is not None:
            self.manager = manager

        if materials is not None:
            for key in materials:
                materials[key] = [i for i in materials[key] if i != "" and i != "None"]
            self.material_types = materials
            log_additional_data("materials", json.dumps(materials))

        log_additional_data("prompt", str(prompt))
        self.decorations = decorations
        if decorations is not None:
            decorations = [i for i in decorations if i != "" and i != "None"]
            log_additional_data("decorations", json.dumps(decorations))

        logger.info(f"{Fore.BLUE}Received prompt: {prompt}{Fore.RESET}")

        await self.get_architect_plan()
        logger.info(f"{Fore.BLUE}Received architect plan {self.plan_list}{Fore.RESET}")

        await self.build_structure()

        logger.info(f"{Fore.BLUE}Received basic structure{Fore.RESET}")

        if request_type is None or request_type.create_windows:
            await self.apply_windows()
            logger.info(f"{Fore.BLUE}Received add-ons{Fore.RESET}")

        if request_type is None or request_type.create_materials:
            await self.get_artist_response()
            logger.info(f"{Fore.BLUE}Received artist response{Fore.RESET}")

        if request_type is None or request_type.apply_post_process:
            await self.apply_style()
            logger.info(f"{Fore.BLUE}Applied style {self.style}{Fore.RESET}")

        if request_type is None or request_type.create_doors:
            await self.apply_doors()
            logger.info(f"{Fore.BLUE}Applied doors{Fore.RESET}")

        if request_type is None or request_type.create_garden:
            await self.create_garden()
            logger.info(f"{Fore.BLUE}Created gardens{Fore.RESET}")

        if request_type is None or request_type.create_decorations:
            await self.decorate()
            logger.info(f"{Fore.BLUE}Obtained decorations{Fore.RESET}")

        self.api_result["result"] = [i.to_json() for i in self.building]
        logger.info(f"{Fore.GREEN}Finished Request{Fore.RESET}")
        return self.api_result

    @sentry_sdk.trace
    async def get_architect_plan(self):
        """Gets the architect's plan for the building"""
        described_layers = ""
        for l in self.layers:
            described_layers += f"{l['name']}: {l['description']}\n"

        self.prompt = await self.llm_client.get_agent_response(
            LLMClient.ARCHITECT,
            self.prompts_file["plan_prompt"].format(self.prompt),
            presets=described_layers,
        )
        self.api_result["architect"] = [l for l in self.prompt.split("\n") if l != ""]
        self.plan_list = [
            i
            for i in self.prompt.split("\n")
            if i.lstrip().lower().startswith(f"layer")
        ]

        sentry_sdk.metrics.distribution(
            key="Layer count",
            value=len(self.plan_list),
            unit="count",
            tags={
                "agent": PalAI.ARCHITECT,
                "service": "PALAI",
            },
        )
        log_additional_data("Architect Plan", "\n".join(self.plan_list))

        return

    @sentry_sdk.trace
    async def build_structure(self):
        for y, l in enumerate(self.plan_list):
            if "|" in l:
                l = l.split("|")[0]
            l = l.split(":")
            if len(l) < 2:
                if self.ws is not None and self.config.getboolean(
                    "socket", "layer", fallback=True
                ):
                    await self.manager.send_personal_message(
                        json.dumps(
                            {
                                "message": "Error processing request",
                                "error": " Unable to read " + str(l),
                            }
                        ),
                        self.ws,
                    )
                return
            chosen_layer = self._get_similarity_response(
                l[1], [i["name"] for i in self.layers]
            )
            logger.info(f"{Fore.BLUE}Chosen Layer: {chosen_layer}{Fore.RESET}")
            blocks = [i for i in self.layers if i["name"] == chosen_layer][0]["blocks"]
            for b in blocks:
                p = Placeable(b.get("type", "CUBE"), b["x"], y, b["z"])
                p.rotation = b.get("rotation", 0)
                self.building.append(p)

        if self.ws is not None and self.config.getboolean(
            "socket", "layer", fallback=True
        ):
            json_building = []
            for l in self.building:
                json_building.append(l.to_json())

            message = {"value": json_building}
            message["event"] = "layer"

            await self.manager.send_personal_message(json.dumps(message), self.ws)

        sentry_sdk.metrics.distribution(
            key="Block Count",
            value=len(self.plan_list),
            unit="count",
            tags={
                "agent": PalAI.ARCHITECT,
                "service": "PALAI",
            },
        )

        logger.info(f"{Fore.BLUE}Received structure.{Fore.RESET}")

    @sentry_sdk.trace
    async def apply_windows(self):
        """Adds doors and windows to the building"""

        plan = "\n".join(self.plan_list)
        add_on_prompt = f"Here is the building:\n{plan}\n"
        # print("ADD ON PROMPT: \n" + str(add_on_prompt))
        logger.debug(f"ADDON PROMPT: {add_on_prompt}")
        styles = ""
        for s in self.windows["styles"]:
            styles += f"{s['name']}:{s['description']}\n"
        windows = await self.llm_client.get_agent_response(
            LLMClient.ADD_ONS,
            add_on_prompt,
            styles=styles,
            quantifiers=self.windows["quantifiers"],
        )
        logger.debug(f"ADDON RESPONSE: {windows}")
        log_additional_data("Add-on Response", windows)
        windows = windows.split("\n")

        height = max([i.y for i in self.building]) + 1
        self.window_styles = [None for _ in range(height)]
        self.window_quantifiers = [None for _ in range(height)]

        style_options = [i["name"] for i in self.windows["styles"]]
        quantifier_options = [i["name"] for i in self.windows["quantifiers"]]
        for line in windows:
            if line.lower().startswith("layer"):
                i = int(line.split(":")[0].split(" ")[1])
                self.window_styles[i] = self._get_similarity_response(
                    line.split(":")[1].split("|")[0].strip(), style_options
                )
                quantifier = self._get_similarity_response(
                    line.split(":")[1].split("|")[1].strip(),
                    quantifier_options,
                )
                self.window_quantifiers[i] = [
                    i["value"]
                    for i in self.windows["quantifiers"]
                    if i["name"] == quantifier
                ][0]

        for i, w in enumerate(self.window_styles):
            if w is None:
                self.window_styles[i] = "none"
                self.window_quantifiers[i] = "none"

        self.building = window_layer.create_windows(
            self.building, self.window_styles, self.window_quantifiers, self.rng
        )

        # Only sending the blocks with add_ons
        self.api_result["add_on_agent"] = windows

        if self.ws is not None and self.config.getboolean(
            "socket", "add_ons", fallback=True
        ):
            json_building = [i.to_json() for i in self.building]
            message = {"value": json_building}
            message["event"] = "add_ons"
            await self.manager.send_personal_message(json.dumps(message), self.ws)

    @sentry_sdk.trace
    async def apply_doors(self):
        doors = door_layer.create_doors(self.building, self.rng)
        sentry_sdk.metrics.distribution(
            key="Door Count",
            value=len(doors),
            unit="count",
            tags={
                "agent": PalAI.ADD_ONS,
                "service": "PALAI",
            },
        )
        log_additional_data("Doors added", str(len(doors)))

        if self.ws is not None and self.config.getboolean(
            "socket", "doors", fallback=True
        ):
            json_building = [i.to_json() for i in doors]
            message = {"value": json_building}
            message["event"] = "doors"
            await self.manager.send_personal_message(json.dumps(message), self.ws)

    @sentry_sdk.trace
    async def create_garden(self):
        self.garden = gardener.create_gardens(self.building, self.rng)
        self.api_result["garden"] = [i.to_json() for i in self.garden]

        sentry_sdk.metrics.distribution(
            key="Garden size",
            value=len(self.garden),
            unit="count",
            tags={
                "agent": PalAI.GARDEN,
                "service": "PALAI",
            },
        )
        log_additional_data("Garden size", str(len(self.garden)))

        if self.ws is not None and self.config.getboolean(
            "socket", "garden", fallback=True
        ):
            json_building = [i.to_json() for i in self.garden]
            message = {"value": json_building}
            message["event"] = "garden"
            await self.manager.send_personal_message(json.dumps(message), self.ws)

    @sentry_sdk.trace
    async def get_artist_response(self):
        materials_response = await self.llm_client.get_agent_response(
            LLMClient.MATERIALS,
            self.original_prompt,
            materials=self.material_types,
            styles=self.post_process.get_available_styles(),
        )

        logger.debug(f"ARTIST RESPONSE: {materials_response}")
        material = {}
        for l in materials_response.split("\n"):
            l = [i.strip() for i in l.upper().split(":")]
            if len(l) == 2:
                if "STYLE" in l[0]:
                    self.style = self._get_similarity_response(
                        l[1].strip(), self.post_process.get_styles_list()
                    )
                    material["STYLE"] = self.style
                elif "FLOOR" in l[0]:
                    material["FLOOR"] = self._get_similarity_response(
                        l[1].strip(), self.material_types["floor"]
                    )
                elif "INTERIOR" in l[0]:
                    material["INTERIOR"] = self._get_similarity_response(
                        l[1].strip(), self.material_types["interior"]
                    )
                elif "EXTERIOR" in l[0]:
                    material["EXTERIOR"] = self._get_similarity_response(
                        l[1].strip(), self.material_types["exterior"]
                    )

        sentry_sdk.metrics.set(
            key="Interior Material",
            value=material["INTERIOR"],
            unit="material",
            tags={
                "agent": PalAI.ARTIST,
                "service": "PALAI",
            },
        )
        sentry_sdk.metrics.set(
            key="Exterior Material",
            value=material["EXTERIOR"],
            unit="material",
            tags={
                "agent": PalAI.ARTIST,
                "service": "PALAI",
            },
        )
        sentry_sdk.metrics.set(
            key="Floor Material",
            value=material["FLOOR"],
            unit="material",
            tags={
                "agent": PalAI.ARTIST,
                "service": "PALAI",
            },
        )
        sentry_sdk.metrics.set(
            key="Style",
            value=material["STYLE"],
            unit="style",
            tags={
                "agent": PalAI.ARTIST,
                "service": "PALAI",
            },
        )

        log_additional_data("Artist response", materials_response)

        self.api_result["materials"] = material
        if self.ws is not None and self.config.getboolean(
            "socket", "material", fallback=True
        ):
            message = {"value": material}
            message["event"] = "material"
            await self.manager.send_personal_message(json.dumps(message), self.ws)

    def _get_similarity_response(self, response, possibilities):
        """Takes in a response and a list of possibilities and returns the most similar possibility

        :param response: unsanitized text
        :type response: str
        :param possibilities: list of possibilities
        :type possibilities: list(str)
        """
        aux = sorted(possibilities, key=lambda x: Levenshtein.distance(x, response))
        return aux[0]

    @sentry_sdk.trace
    async def apply_style(self):
        """Applies the style received from the artist"""
        try:
            self.post_process.import_building(self.building)
            self.building = self.post_process.style(self.style)
        except Exception as e:
            self.style = "no style"
            logger.warning(f"{Fore.RED}Style Error {e}{Fore.RESET}")
            await self.manager.send_personal_message(
                json.dumps("Error found with post-processing"), self.ws
            )

    @sentry_sdk.trace
    async def decorate(self):
        decorator = Decorator(self.rng, self.decorations)
        decorator.import_building(self.building)
        self.decorations = decorator.decorate()

        self.api_result["decorations"] = self.decorations

        sentry_sdk.metrics.distribution(
            key="Decorations",
            value=len(self.decorations),
            unit="count",
            tags={
                "agent": PalAI.DECORATOR,
                "service": "PALAI",
            },
        )
        log_additional_data("Decorations added", str(len(self.decorations)))

        if self.ws is not None and self.config.getboolean(
            "socket", "decorations", fallback=True
        ):
            message = {"value": self.decorations}
            message["event"] = "decorations"
            await self.manager.send_personal_message(json.dumps(message), self.ws)

    def overlap_blocks(
        self, base_structure: list[Placeable], extra_blocks: list[Placeable]
    ):
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
            if (
                len(
                    [
                        i
                        for i in base_structure
                        if (i.x == b.x and i.y == b.y and i.z == b.z)
                    ]
                )
                == 0
            ):
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
        building_info: list[str] = []

        # match lines that have two `|` characters
        for line in lines:
            if line.startswith("B:"):
                try:
                    if level is not None:
                        line += f"|{level}"  # if a level is given then it is not present in the script at this point
                    line = line.split(" ")[
                        0
                    ]  # sometimes LLMs return garbage after the immportant part
                    building_info.append(line[2:])
                except Exception as e:
                    logger.warning(
                        f"{Fore.RED}Error extracting building information from LLM response.{Fore.RESET}"
                    )

        blocks: list[Placeable] = []
        for block in building_info:
            try:
                block = block.split("|")
                if len(block) > 2:
                    position = block[1].split(",")
                    b_type = Placeable.BlockType.from_str(block[0])
                    aux = Placeable(
                        b_type, int(position[1]), int(block[2]), int(position[0])
                    )
                    blocks.append(aux)
            except Exception as e:
                logger.warning(
                    f"{Fore.RED}Error extracting building information from LLM response:{Fore.RESET}{e}"
                )
                continue
        return blocks
