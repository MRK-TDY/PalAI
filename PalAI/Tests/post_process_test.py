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
        building = [Placeable("CUBE", 0, 0, 0,), Placeable("CUBE", 0, 2, 2)]

        pp = PostProcess()
        pp.import_building(building)

        pp.style(list(pp.styles.keys())[0])
        building = pp.export_building()
        self.assertEqual(len(building), 1)

    def test_does_not_remove_entire_building(self):
        building = [Placeable("CUBE", 0, 0, 0,)]

        pp = PostProcess()
        pp.import_building(building)

        pp.style(list(pp.styles.keys())[0])
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


    # building = get_square_building(5)
    #
    # print(f"{Fore.CYAN}Original Building:{Style.RESET_ALL}")
    # # This one is correct, should point up at the top left corner
    # building[0]["tags"] = {"type": "DOOR", "position": "(-1,0,0)"}
    # # This one is incorrect, points down at the top right corner, should be changed to point up
    # building[6]["tags"] = {"type": "DOOR", "position": "(2,0,1)"}
    # # This one is incorrect, points down at the center, should keep pointing down but be moved down
    # building[4]["tags"] = {"type": "DOOR", "position": "(1,0,0)"}
    # building[8]["tags"] = {"type": "DOOR", "position": "(2,0,3)"}
    # pretty_print_addons(building)
    # print(f"{Fore.CYAN}Post Processed Building:{Style.RESET_ALL}")
    # pp = PostProcess()
    # pp.import_building(building)
    # pp.clean_add_ons()
    # building = pp.grid_to_json()
    # pretty_print_addons(building)

if __name__ == '__main__':
    unittest.main()
