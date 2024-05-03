import os
import json
import unittest
from PalAI.Server.placeable import Placeable
from PalAI.Server.decorator import Decorator

class PostProcessTest(unittest.TestCase):

    def _get_square_building(self, size):
        building = []
        for x in range(size):
            for z in range(size):
                block = Placeable("CUBE", x, 0, z)
                building.append(block)

        return building

    def test_decorations_are_placed(self):
        building = self._get_square_building(3)
        decorator = Decorator()
        decorator.import_building(building)
        decorations = decorator.decorate()
        self.assertGreater(len(decorations),  0)

    def test_all_decorations_are_used(self):
        with open(os.path.join(os.path.dirname(__file__), '../Server/decorations.json')) as f:
            decorations_json = json.load(f)

        used_decorations = set()
        total_decorations_count = 0
        for d in decorations_json["decorations"]:
            total_decorations_count += len(d.get("asset_name", [d["name"]]))

        for _ in range(100):
            building = self._get_square_building(5)
            decorator = Decorator()
            decorator.import_building(building)
            decorations = decorator.decorate()

            # Get the json list of decorations
            # print(json.dumps(decorations, indent=4))
            for d in decorations:
                found = False
                for prefab in decorations_json["decorations"]:
                    if d["type"] in prefab.get("asset_name", [prefab["name"]]):
                        found = True
                        break

                if not found:
                    self.fail("Decoration not found in decorations.json")

                used_decorations.add(d["type"])
                if len(used_decorations) == total_decorations_count:
                    # Test passes
                    return

        self.assertEqual(len(used_decorations), total_decorations_count)


    def test_decorations_are_correct(self):
        with open(os.path.join(os.path.dirname(__file__), '../Server/decorations.json')) as f:
            decorations_json = json.load(f)

        # Repeat test multiple times
        for _ in range(100):
            building = self._get_square_building(5)
            decorator = Decorator()
            decorator.import_building(building)
            decorations = decorator.decorate()


            # Get the json list of decorations
            # print(json.dumps(decorations, indent=4))
            for d in decorations:
                found = False
                for prefab in decorations_json["decorations"]:
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
                        self.assertTrue(nx >= 0 and nx < 5 and nz >= 0 and nz < 5)
                    elif r == "WALL":
                        self.assertTrue(nx < 0 or nx >= 5 or nz < 0 or nz >= 5)

if __name__ == '__main__':
    unittest.main()
