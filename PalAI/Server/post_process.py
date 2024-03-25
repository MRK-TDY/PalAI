import os
import numpy as np
import json
from collections import deque


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
            styles += f"{s}: {self.styles['styles'][s]['description']}\n"
        return styles

    def fill_empty_spaces(self):
        label = 0
        neighbors = [(0, 0, 1), (0, 0, -1), (0, 1, 0), (0, -1, 0),
                     (1, 0, 0), (-1, 0, 0)]
        building_array = np.copy(self.pixel_grid)

        #pad outside of the building such that all empty spaces on the edges are connected
        building_array = np.pad(building_array, ((0, 1), (1, 1), (1, 1)), mode='constant', constant_values=-1)
        yDim, xDim, zDim = building_array.shape

        labelArray = np.zeros_like(building_array)
        statusArray = np.zeros_like(building_array, dtype=bool)

        for k in range(yDim):  # Apply the algorithm layer by layer
            for i in range(xDim):
                for j in range(zDim):
                    if not statusArray[k, i, j]:
                        if building_array[k, i, j] == -1:  # empty space
                            label += 1
                            queue1 = deque()
                            queue1.append((k, i, j))
                            while queue1:
                                y, x, z = queue1.popleft()
                                if not statusArray[y, x, z]:
                                    statusArray[y, x, z] = True
                                    labelArray[y, x, z] = label
                                    if label > 1:
                                        # found empty space, fill it in
                                        self.grid[k][i - 1][j - 1] = {
                                                "type": "CUBE",
                                                "position": f"({i - 1}, {k}, {j - 1})"
                                                }
                                        self.pixel_grid[k, i - 1, j - 1] = 1
                                    for dy, dx, dz in neighbors:
                                        ny, nx, nz = y +dy, x + dx, z + dz
                                        if 0 <= nx < xDim and 0 <= nz < zDim \
                                            and 0 <= ny < yDim \
                                            and not statusArray[ny, nx, nz] \
                                            and building_array[ny, nx, nz] == -1:
                                            queue1.append((ny, nx, nz))


    def style(self, style):
        self.remove_floating_blocks()
        self.fill_empty_spaces()
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

    def remove_floating_blocks(self):
        # TODO: edge case where building is a single block deletes building

        # Remove blocks that are not supported by any other block
        floating_block_kernel = [
                [[0, 0, 0],
                 [0, -1, 0],
                 [0, 0, 0]],

                [[0, -1, 0],
                 [-1, 1, -1],
                 [0, -1, 0]],

                [[0, 0, 0],
                 [0, -1, 0],
                 [0, 0, 0]]]
        matching_positions = self.apply_kernel(floating_block_kernel)
        for c in matching_positions:
            self.grid[c[0][0]][c[0][1]][c[0][2]] = None
            self.pixel_grid[c[0][0], c[0][1], c[0][2]] = -1

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
            new_filter = []
            for f in filter_matrix:
                if rotation == 0:  # 0 degrees, no rotation
                    new_filter.append(f)
                elif rotation == 1:  # 90 degrees
                    new_filter.append([list(row) for row in zip(*f[::-1])])
                elif rotation == 2:  # 180 degrees
                    new_filter.append([row[::-1] for row in f[::-1]])
                elif rotation == 3:  # 270 degrees
                    new_filter.append([list(row) for row in zip(*f)][::-1])
            return new_filter

        if not isinstance(filter_matrix[0][0], list):
            filter_matrix = [filter_matrix]

        filter_height = len(filter_matrix)
        filter_depth = len(filter_matrix[0])
        filter_width = len(filter_matrix[0][0])

        # Assume the filter dimensions are odd sizes
        height_offset = filter_height // 2
        depth_offset = filter_depth // 2
        width_offset = filter_width // 2

        filtered_values = []

        for y in range(self.size_y):
            for x in range(self.size_x):
                for z in range(self.size_z):
                    for orientation in range(4):
                        rotated_filter = rotate_filter(filter_matrix, orientation)
                        applies = True
                        for fh in range(filter_height):
                            for fd in range(filter_depth):
                                for fw in range(filter_width):
                                    ny, nx, nz = y + fh - height_offset, x + fw - width_offset, z + fd - depth_offset
                                    # Check bounds
                                    if 0 <= ny < self.size_y and 0 <= nx < self.size_x and 0 <= nz < self.size_z:
                                        value = self.pixel_grid[ny][nx][nz]
                                    else:
                                        value = -1  # Outside bounds, treat as empty space

                                    if rotated_filter[fh][fd][fw] != 0 and rotated_filter[fh][fd][fw] != value:
                                        applies = False
                                        break
                                if not applies:
                                    break
                            if not applies:
                                break

                        if applies:
                            filtered_values.append(((y, x, z), orientation))
                            break # only first orientation matches

        return filtered_values



    def get_block_dict_position(self, block):
        position = block["position"].replace("(", "").replace(")", "").split(",")
        return [eval(x) for x in position]
