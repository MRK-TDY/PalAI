import os
import json
import random
import unittest
from PalAI.Server.placeable import Placeable
from PalAI.Server.decorator import Decorator
from hypothesis import given, settings, strategies as st


@st.composite
def square_building_strategy(draw):
    building = []
    for y in range(draw(st.integers(min_value=1, max_value=3))):
        size = draw(st.integers(min_value=4, max_value=8))
        offset = (draw(st.integers(min_value=-5, max_value=5)),
                  draw(st.integers(min_value=-5, max_value=5)))
        building.extend(_get_square_building(size, offset, y))

    return building


def _get_square_building(size, offset, height = 0):
    building = []
    for x in range(size):
        for z in range(size):
            block = Placeable("CUBE", x + offset[0], height, z + offset[1])
            building.append(block)

    return building

class PostProcessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with open(
            os.path.join(os.path.dirname(__file__), "../Server/decorations.json")
        ) as f:
            cls.decorations_json = json.load(f)

    @given(square_building_strategy(), st.randoms())
    @settings(max_examples=100)
    def test_decorations_are_placed(self, building, rng):
        decorator = Decorator(random.Random())
        decorator.import_building(building)
        decorations = decorator.decorate()
        self.assertGreater(len(decorations), 0)

    def test_all_decorations_are_used_within_limits(self):
        used_decorations = set()
        total_decorations_count = 0
        decoration_names = set()
        decoration_limits = {}

        for d in self.decorations_json["decorations"]:
            total_decorations_count += len(d.get("asset_name", [d["name"]]))
            decoration_names = decoration_names.union(d.get("asset_name", [d["name"]]))

        for _ in range(100):
            building = _get_square_building(5, (0, 0))
            decorator = Decorator(random.Random())
            decorator.import_building(building)
            decorations = decorator.decorate()

            # Get the json list of decorations
            # print(json.dumps(decorations, indent=4))
            for d in decorations:
                found = False
                for prefab in self.decorations_json["decorations"]:
                    if d["type"] in prefab.get("asset_name", [prefab["name"]]):
                        found = True
                        break

                if not found:
                    self.fail("Decoration not found in decorations.json")

                used_decorations.add(d["type"])
                if len(used_decorations) == total_decorations_count:
                    # Test passes
                    return

        self.assertEqual(
            len(used_decorations),
            total_decorations_count,
            f"{[i for i in decoration_names if i not in used_decorations]} not used",
        )

    @given(square_building_strategy(), st.randoms())
    @settings(max_examples=100)
    def test_decorations_are_correct(self, building, rng):
        decorator = Decorator(random.Random())
        decorator.import_building(building)
        decorations = decorator.decorate()

        ground_floor = [b for b in building if b.y == 0]
        min_x = min(ground_floor, key=lambda b: b.x).x
        min_z = min(ground_floor, key=lambda b: b.z).z
        max_x = max(ground_floor, key=lambda b: b.x).x
        max_z = max(ground_floor, key=lambda b: b.z).z

        # Get the json list of decorations
        # print(json.dumps(decorations, indent=4))
        for d in decorations:
            found = False
            for prefab in self.decorations_json["decorations"]:
                if d["type"] in prefab.get("asset_name", [prefab["name"]]):
                    matching_prefab = prefab
                    found = True
                    break

            if not found:
                self.fail("Decoration not found in decorations.json")

            adjacencies = matching_prefab["adjacency"]
            for _ in range(d["rotation"]):
                adjacencies = [adjacencies[3]] + adjacencies[:3]

            pos = d["position"].replace("(", "").replace(")", "").split(",")
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            x = int(pos[0])
            z = int(pos[2])

            for i, r in enumerate(adjacencies):
                dx, dz = directions[i]
                nx, nz = x + dx, z + dz
                if r == "EMPTY":
                    self.assertTrue(nx >= min_x and nx <= max_x and nz >= min_z and nz <= max_z)
                elif r == "WALL":
                    self.assertTrue(nx < min_x or nx > max_x or nz < min_z or nz > max_z)


if __name__ == "__main__":
    unittest.main()
