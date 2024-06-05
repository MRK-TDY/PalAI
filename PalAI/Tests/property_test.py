import asyncio
from copy import copy
import json
import logging
import os
import unittest

from hypothesis import event, given, settings
from hypothesis import strategies as st
import yaml

from PalAI.Server.pal_ai import PalAI
from PalAI.Server.placeable import Placeable
from PalAI.Server.visualizer import ObjVisualizer
from PalAI.Tools.LLMClients.strategy_client import StrategyClient


@st.composite
def building_strategy(draw):
    """Generate an API result for each run of the suite."""

    with open(
        os.path.join(os.path.dirname(__file__), "../../prompts.yaml"), "r"
    ) as file:
        prompts_file = yaml.safe_load(file)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.WARNING)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter("%(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    client = StrategyClient(prompts_file, logger, draw=draw)

    rng = draw(st.randoms())
    pal = PalAI(prompts_file, client, logger)
    pal.rng = rng

    prompt = "Where we're going we don't need prompts."
    response = asyncio.run(pal.build(prompt))

    # We need to be able to identify which buildings are failing
    response["id"] = draw(st.integers(min_value=0, max_value=1000000))
    return response


def generate_obj(building, response, name="test"):
    obj = ObjVisualizer().generate_obj(building)

    with open(os.path.join(os.path.dirname(__file__), f"{name}.obj"), "w") as fptr:
        fptr.write(obj)
        fptr.flush()

    with open(os.path.join(os.path.dirname(__file__), f"{name}.json"), "w") as fptr:
        fptr.write(json.dumps(response, indent=2))
        fptr.flush()


class PropertyTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # delete the test_results folderl
        os.makedirs(
            os.path.join(os.path.dirname(__file__), "test_results"), exist_ok=True
        )
        # delete all files in the test_results folder
        for file in os.listdir(os.path.join(os.path.dirname(__file__), "test_results")):
            os.remove(os.path.join(os.path.dirname(__file__), "test_results", file))

        return super().setUpClass()

    @given(building_strategy())
    @settings(max_examples=500)
    def test_complete_pipeline(self, api_response):
        # Extract building from the response
        building = [Placeable.from_json(i) for i in api_response["result"]]
        garden = [Placeable.from_json(i) for i in api_response["garden"]]
        gardened_building = copy(garden)
        gardened_building.extend(building)

        # Statistics
        building_size = len(building) - (len(building) % 25)
        garden_size = len(garden) - (len(garden) % 10)
        event(f"Building size: {building_size}-{building_size + 24}")
        event(f"Garden size: {garden_size}-{garden_size + 9}")

        # Save the building for future reference
        generate_obj(
            gardened_building, api_response, "test_results/" + str(api_response["id"])
        )

        # Assert tests
        self.assert_ground_floor(building)
        self.assert_doors_in_ground_floor(building)
        self.assert_door_exists(building)
        self.assert_maximum_garden_size(garden)
        self.assert_garden_light_count(garden)

    def assert_door_exists(self, building: list[Placeable]):
        for i in building:
            if i.has_door():
                return
        self.fail("No door found in building")

    def assert_doors_in_ground_floor(self, building: list[Placeable]):
        for i in building:
            if i.has_door() and i.y != 0:
                self.fail(f"Found door outside ground floor: {i.to_json()}")
        return # No doors found outside the ground floor

    def assert_ground_floor(self, building: list[Placeable]):
        for i in building:
            if i.y == 0:
                return
        self.fail("No door found in building")

    def assert_maximum_garden_size(self, garden: list[Placeable]):
        max_size = 25
        self.assertLess(len(garden), max_size, f"Garden size exceeds {max_size}")

    def assert_garden_light_count(self, garden: list[Placeable]):
        lights = [i for i in garden if i.block_type == Placeable.BlockType.GARDEN_LIGHT]
        self.assertLessEqual(len(lights), 4, f"Too many garden lights, found {len(lights)}")
        # self.assertNotEqual(len(lights), 3, f"Invalid number of lights, should be 1, 2 or 4")


if __name__ == "__main__":
    unittest.main()
