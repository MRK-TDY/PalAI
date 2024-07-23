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
