import numpy as np


class PostProcess:
    def __init__(self, building):
        positions = [self.get_block_dict_position(b) for b in building]

        self.size_x = max(positions, key=lambda x: x[0])[0] + 1
        self.size_y = max(positions, key=lambda x: x[1])[1] + 1
        self.size_z = max(positions, key=lambda x: x[2])[2] + 1

        # Grid is indexed (y, x, z) because most transformations happen on a slice of the y axis
        self.grid = [
            [[None for _ in range(self.size_z)] for _ in range(self.size_x)]
            for _ in range(self.size_y)
        ]
        self.pixel_grid = np.zeros((self.size_y, self.size_x, self.size_z), dtype=int)

        for b in building:
            pos = self.get_block_dict_position(b)
            self.grid[pos[1]][pos[0]][pos[2]] = b
            self.pixel_grid[pos[1], pos[0], pos[2]] = 1

    def style(self):
        corners = self.detect_corners()
        for c in corners:
            self.grid[c[0][0]][c[0][1]][c[0][2]]["type"] = "DIAGONAL"
            self.grid[c[0][0]][c[0][1]][c[0][2]]["rotation"] = c[1]

    def grid_to_json(self):
        json = []
        for yz in self.grid:
            for z in yz:
                for b in z:
                    if b is not None:
                        json.append(b)

        return json

    def detect_corners(self):
        corners = []
        # Iterate over each y-level
        for y in range(self.size_y):
            # Iterate over the x and z plane
            for x in range(self.size_x):
                for z in range(self.size_z):
                    if self.pixel_grid[y, x, z] == 1:
                        # Check the 4 direct neighbors
                        neighbors = [
                            (x - 1, z),  # Left
                            (x + 1, z),  # Right
                            (x, z - 1),  # Down
                            (x, z + 1),  # Up
                        ]
                        # Count how many of these neighbors are filled
                        filled_neighbors = sum(
                            1
                            for nx, nz in neighbors
                            if 0 <= nx < self.size_x
                            and 0 <= nz < self.size_z
                            and self.pixel_grid[y, nx, nz] == 1
                        )

                        if filled_neighbors == 2:
                            # Determine the orientation based on which neighbors are filled
                            filled_positions = [
                                (nx, nz)
                                for nx, nz in neighbors
                                if 0 <= nx < self.size_x
                                and 0 <= nz < self.size_z
                                and self.pixel_grid[y, nx, nz] == 1
                            ]
                            # Orientation determination (simplified, example logic)
                            if (x + 1, z) in filled_positions and (
                                x,
                                z + 1,
                            ) in filled_positions:
                                orientation = 3  # Lower-right corner
                            elif (x - 1, z) in filled_positions and (
                                x,
                                z + 1,
                            ) in filled_positions:
                                orientation = 2  # Lower-left corner
                            elif (x + 1, z) in filled_positions and (
                                x,
                                z - 1,
                            ) in filled_positions:
                                orientation = 0  # Upper-left corner
                            elif (x - 1, z) in filled_positions and (
                                x,
                                z - 1,
                            ) in filled_positions:
                                orientation = 1  # Upper-right corner
                            else:
                                orientation = (
                                    -1
                                )  # Undefined or not a corner by our criteria

                            if orientation != -1:
                                corners.append(((y, x, z), orientation))

        return corners

    def get_block_dict_position(self, block):
        position = block["position"].replace("(", "").replace(")", "").split(",")
        return [eval(x) for x in position]
