import json
import unittest

from PalAI.Server.pal_ai import *

class ExtractInfoTest(unittest.TestCase):

    def test_simple(self):
        request = """LAYER:
            0 0 | 0 0
            0 1 1 1 0
            0 | 1 | 0
            0 1 1 1 0
            END LAYER:""".replace("  ", "")
        pal = PalAI.create_default()
        building = pal.extract_building_information(request, 0)

        print(json.dumps(building, indent = 2))



if __name__ == '__main__':
    unittest.main()
