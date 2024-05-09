import random
import unittest
from PalAI.Server.placeable import Placeable
from PalAI.Server.post_process import PostProcess


class PostProcessTest(unittest.TestCase):

    def _get_square_building(self, size):
        building = []
        for x in range(size):
            for z in range(size):
                block = Placeable("CUBE", x, 0, z)
                building.append(block)

        return building

    def test_removes_floating_block(self):
        building = [
            Placeable(
                "CUBE",
                0,
                0,
                0,
            ),
            Placeable("CUBE", 0, 2, 2),
        ]

        pp = PostProcess()
        pp.import_building(building)

        pp.style(random.choice(pp.get_styles_list()))
        building = pp.export_building()
        self.assertEqual(len(building), 1)

    def test_does_not_remove_entire_building(self):
        building = [
            Placeable(
                "CUBE",
                0,
                0,
                0,
            )
        ]

        pp = PostProcess()
        pp.import_building(building)

        pp.style(random.choice(pp.get_styles_list()))
        building = pp.export_building()
        self.assertEqual(len(building), 1)

    def test_applies_rounded_style(self):
        building = self._get_square_building(3)

        pp = PostProcess()
        pp.import_building(building)

        pp.style("rounded")
        building = pp.export_building()
        corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
        for p in building:
            if (p.x, p.z) in corners:
                self.assertEqual(p.block_type, "ROUNDED CORNER")
            else:
                self.assertEqual(p.block_type, "CUBE")

    def test_overrides_block_type(self):
        building = [
            Placeable(
                "DIAGONAL",
                0,
                0,
                0,
            ),
            Placeable(
                "DIAGONAL",
                1,
                0,
                0,
            ),
            Placeable(
                "DIAGONAL",
                0,
                0,
                1,
            ),
            Placeable(
                "DIAGONAL",
                1,
                0,
                1,
            ),
        ]

        pp = PostProcess()
        pp.import_building(building)

        pp.style("blocky")
        building = pp.export_building()
        for p in building:
            self.assertEqual(
                p.block_type, "DIAGONAL", "blocky style shoould not change block type"
            )

        pp.style("rounded")
        building = pp.export_building()
        rotations = set()
        for p in building:
            self.assertNotIn(p.rotation, rotations)
            rotations.add(p.rotation)
            self.assertEqual(
                p.block_type, "ROUNDED CORNER", "rounded style should update block type"
            )

    def test_applies_modern_style(self):
        building = self._get_square_building(3)

        pp = PostProcess()
        pp.import_building(building)

        pp.style("modern")
        building = pp.export_building()
        corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
        for p in building:
            if (p.x, p.z) in corners:
                self.assertEqual(p.block_type, "DIAGONAL")
            else:
                self.assertEqual(p.block_type, "CUBE")

    def test_fill_empty_spaces(self):
        building = self._get_square_building(3)
        del building[4]

        pp = PostProcess()
        pp.import_building(building)

        pp.style("blocky")
        building = pp.export_building()
        self.assertEqual(len(building), 8, "building is open to the sky, it shouldn't be filled in")

        top_floor = self._get_square_building(3)
        for p in top_floor:
            p.y = 1
        building.extend(top_floor)

        pp.import_building(building)
        pp.style("blocky")
        building = pp.export_building()
        self.assertEqual(len(building), 18)

    def test_removes_excess_blocks(self):
        building = self._get_square_building(3)
        building.append(Placeable("CUBE", 0, 0, 0))

        pp = PostProcess()
        pp.import_building(building)

        pp.style("blocky")
        building = pp.export_building()
        self.assertEqual(len(building), 9)

    def test_rounded_style(self):
        pp = PostProcess()
        seen_block_types = set()

        # when a block is rotated, there aren't any blocks on the direction of the rotation
        # this is also true for the next index over, as the blocks are corners
        rotation_index = ((1, 0), (0, 1), (-1, 0), (0, -1))

        for _ in range(20):
            building = []

            for x in range(10):
                for y in range(5):
                    for z in range(10):
                        if random.random() < 0.5:
                            building.append(Placeable("CUBE", x, y, z))

            pp.import_building(building)
            pp.style("rounded")
            building = pp.export_building()
            for p in building:
                seen_block_types.add(p.block_type)
                self.assertIn(p.rotation, [0, 1, 2, 3])

                if p.block_type == "ROUNDED CORNER":
                    free_positions = [(p.x + rotation_index[p.rotation][0], p.z + rotation_index[p.rotation][1]),]
                                      # (p.x + rotation_index[(p.rotation + 1) % 4][0], p.z + rotation_index[(p.rotation + 1) % 4][1])]
                    for p2 in building:
                        if (p2.x, p2.z) in free_positions and p2.y == p.y:
                            self.fail("There are blocks in the direction of the rotation")


        self.assertEqual(seen_block_types, {"CUBE", "ROUNDED CORNER", "CYLINDER"})



    def test_property_rotation(self):
        seen_rotations = set()
        pp = PostProcess()
        for style in list(pp.get_styles_list()):
            for _ in range(20):
                building = []
                for x in range(10):
                    for y in range(5):
                        for z in range(10):
                            if random.random() < 0.5:
                                building.append(Placeable("CUBE", x, y, z))

                pp.import_building(building)
                pp.style(style)
                building = pp.export_building()
                for p in building:
                    seen_rotations.add(p.rotation)
                    self.assertIn(p.rotation, [0, 1, 2, 3])

        if len(seen_rotations) != 4:
            self.fail("Not all rotations were used")

if __name__ == "__main__":
    unittest.main()
