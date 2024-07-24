from loguru import logger
import os
import sys
import yaml
from PalAI.Server.pal_ai import PalAI
import asyncio
import unittest


class TestClient(unittest.TestCase):
    """This class tests the entire PalAI flow using objective prompts.
    The goal is to ensure that the LLM is capable of generating the requested structure."""

    def _create_pal_ai(self):
        os.chdir(os.path.dirname(__file__))

        llm_client = "gpt"
        with open(
            os.path.join(os.path.dirname(__file__), "../../prompts.yaml"), "r"
        ) as file:
            prompts_file = yaml.safe_load(file)

        pal_ai = PalAI(prompts_file, llm_client)

        return pal_ai

    def _build_structure(self, prompt):
        pal_ai = self._create_pal_ai()

        pal_ai.prompt = prompt
        asyncio.run(pal_ai.get_architect_plan())
        pal_ai.build_structure()

        return pal_ai, pal_ai.building

    @unittest.skip("This test depends on the LLM, it does not need to be run every time")
    def test_small_house(self):
        _, building = self._build_structure(
            "I want a house that is just a 2x2 square flat on the ground with a single floor"
        )

        self.assertEqual(len(building), 4, "building should only have 4 blocks")

        positions = []
        for b in building:
            positions.append(
                [
                    eval(x)
                    for x in b["position"].replace("(", "").replace(")", "").split(",")
                ]
            )

        hashable_positions = [tuple(p) for p in positions]
        self.assertEqual(
            len(hashable_positions),
            len(set(hashable_positions)),
            "there shouldn't be repeated positions",
        )
        self.assertEqual(
            len(list(filter(lambda x: x[1] == 0, positions))),
            4,
            "all blocks should touch the ground",
        )

        min_x, min_z = positions[0][0], positions[0][2]
        max_x, max_z = positions[0][0], positions[0][2]
        for p in positions:
            if p[0] < min_x:
                min_x = p[0]
            if p[0] > max_x:
                max_x = p[0]
            if p[2] < min_z:
                min_z = p[2]
            if p[2] > max_z:
                max_z = p[2]

        self.assertEqual(max_x - min_x, 1, "shape created should be a 2x2 square")
        self.assertEqual(max_z - min_z, 1, "shape created should be a 2x2 square")

    @unittest.skip("This test depends on the LLM, it does not need to be run every time")
    def test_artist(self):
        pal_ai = self._create_pal_ai()
        pal_ai.prompt = "I want a very rounded house with no sharp angles, use a very generic type of bland white for the floor, for the interior use a honeycomb of the same color, and for the exterior use a material that is found naturally on the beach."
        pal_ai.original_prompt = pal_ai.prompt
        asyncio.run(pal_ai.get_artist_response())

        artist_response = pal_ai.api_result["materials"]
        self.assertEqual(artist_response["STYLE"].upper(), "ROUNDED", "style should be curves")
        self.assertEqual(
            artist_response["FLOOR"], "GENERIC WHITE", "floor material doesn't match"
        )
        self.assertEqual(
            artist_response["INTERIOR"].upper(),
            "HONEYCOMB WHITE",
            "interior material doesn't match",
        )
        self.assertEqual(
            artist_response["EXTERIOR"].upper(), "SAND", "exterior material doesn't match"
        )


if __name__ == "__main__":
    unittest.main()
