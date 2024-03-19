import os
import numpy as np
import json


class PostProcess:
    def __init__(self, style_sheet = "styles.json"):

        with open(os.path.join(os.path.dirname(__file__), style_sheet), 'r') as fptr:
            self.styles = json.load(fptr)

    def import_building(self, building):
        positions = [self.get_block_dict_position(b) for b in building]

        self.size_x = max(positions, key=lambda x: x[0])[0] + 1
        self.size_y = max(positions, key=lambda x: x[1])[1] + 1
        self.size_z = max(positions, key=lambda x: x[2])[2] + 1

        # Grid is indexed (y, x, z) because most transformations happen on a slice of the y axis
        self.grid = [
            [[None for _ in range(self.size_z)] for _ in range(self.size_x)]
            for _ in range(self.size_y)
        ]
        self.pixel_grid = np.ones((self.size_y, self.size_x, self.size_z), dtype=int) * -1

        for b in building:
            pos = self.get_block_dict_position(b)
            self.grid[pos[1]][pos[0]][pos[2]] = b
            self.pixel_grid[pos[1], pos[0], pos[2]] = 1

    def get_available_styles(self):
        styles = ""
        for s in self.styles["styles"].keys():
            styles += f"{s}: {self.styles["styles"][s]['description']}\n"
        return styles

    def style(self, style):
        for rule in self.styles["styles"][style]["rules"]:
            matching_positions = self.apply_kernel(rule["filter"])
            for effect in rule["effects"]:
                for c in matching_positions:
                    placeholders = { "rotation" : int(c[1]) }
                    block = self.grid[c[0][0]][c[0][1]][c[0][2]]
                    block[effect["key"]] = effect["value"].format_map(placeholders)
                    if block[effect["key"]].isdigit():
                        block[effect["key"]] = int(block[effect["key"]])
        return self.grid_to_json()

    def grid_to_json(self):
        json = []
        for yz in self.grid:
            for z in yz:
                for b in z:
                    if b is not None:
                        json.append(b)

        return json

    def apply_kernel(self, filter_matrix):
        def rotate_filter(filter_matrix, rotation):
            # Rotate the filter matrix according to the rotation value (0, 90, 180, 270 degrees)
            if rotation == 0:  # 0 degrees, no rotation
                return filter_matrix
            elif rotation == 1:  # 90 degrees
                return [list(row) for row in zip(*filter_matrix[::-1])]
            elif rotation == 2:  # 180 degrees
                return [row[::-1] for row in filter_matrix[::-1]]
            elif rotation == 3:  # 270 degrees
                return [list(row) for row in zip(*filter_matrix)][::-1]

        filtered_values = []
        filter_size = len(filter_matrix)

        # Assume the filter is square and of odd size
        offset = filter_size // 2

        for y in range(self.size_y):
            for x in range(self.size_x):
                for z in range(self.size_z):

                    for orientation in range(4):
                        rotated_filter = rotate_filter(filter_matrix, orientation)
                        applies = True
                        for fy in range(filter_size):
                            for fx in range(filter_size):
                                nx, nz = x + fx - offset, z + fy - offset
                                if 0 <= nx < self.size_x and 0 <= nz < self.size_z:
                                    value = self.pixel_grid[y][nx][nz]
                                else:
                                    value = -1

                                if rotated_filter[fy][fx] != 0 and rotated_filter[fy][fx] != value:
                                    applies = False
                        if applies:
                            filtered_values.append(((y, x, z), orientation))

        return filtered_values

    def get_block_dict_position(self, block):
        position = block["position"].replace("(", "").replace(")", "").split(",")
        return [eval(x) for x in position]
