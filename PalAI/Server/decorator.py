import numpy as np
import json
import os

class Decorator:
    def __init__(self, style_sheet = "styles.json"):
        with open(os.path.join(os.path.dirname(__file__), style_sheet), 'r') as fptr:
            self.decorations = json.load(fptr)

    def import_building(self, api_building):
        to_remove = []
        for b in api_building:
            if b["type"] != "CUBE":
                to_remove.append(b)

        for i in to_remove:
            api_building.remove(i)

        positions = [self.get_block_dict_position(b) for b in api_building]

        self.size_x = max(positions, key=lambda x: x[0])[0] + 1
        self.size_y = max(positions, key=lambda x: x[1])[1] + 1
        self.size_z = max(positions, key=lambda x: x[2])[2] + 1

        # Grid is indexed (y, x, z) because most transformations happen on a slice of the y axis
        self.grid = [
            [[None for _ in range(self.size_z)] for _ in range(self.size_x)]
            for _ in range(self.size_y)
        ]
        self.pixel_grid = np.ones((self.size_y, self.size_x, self.size_z), dtype=int) * -1

        for b in api_building:
            pos = self.get_block_dict_position(b)
            self.grid[pos[1]][pos[0]][pos[2]] = b
            self.pixel_grid[pos[1], pos[0], pos[2]] = 1

        # Remove blocks on top of existing blocks, we are only interested in floors
        for b in api_building:
            pos = self.get_block_dict_position(b)
            for y in range(pos[1] + 1, self.size_y):
                if self.grid[y][pos[0]][pos[2]] is not None:
                    self.grid[y][pos[0]][pos[2]] = None
                    self.pixel_grid[y][pos[0]][pos[2]] = -1
                else:
                    break #If there is an empty space above a block there may be another floor above




    def get_block_dict_position(self, block):
        position = block["position"].replace("(", "").replace(")", "").split(",")
        return [eval(x) for x in position]
