import os
import numpy as np
import json
from collections import deque


class PostProcess:
    def __init__(self, style_sheet="styles.json"):
        """Responsible for applying post-processing and style rules to a building

        :param style_sheet: list of available styles
        :type style_sheet: (str) relative path to the style sheet json
        """
        with open(os.path.join(os.path.dirname(__file__), style_sheet), "r") as fptr:
            self.styles = json.load(fptr)

    def import_building(self, building):
        """Imports a building from a list of blocks, required to be called before applying any style rules

        :param building: building to be imported
        :type building: list(dict) list of blocks
        """
        positions = [self.get_block_dict_position(b) for b in building]

        self.size_x = max(positions, key=lambda x: x[0])[0] + 1
        self.size_y = max(positions, key=lambda x: x[1])[1] + 1
        self.size_z = max(positions, key=lambda x: x[2])[2] + 1

        # Grid is indexed (y, x, z) because most transformations happen on a slice of the y axis
        self.grid = [
            [[None for _ in range(self.size_z)] for _ in range(self.size_x)]
            for _ in range(self.size_y)
        ]
        self.pixel_grid = (
            np.ones((self.size_y, self.size_x, self.size_z), dtype=int) * -1
        )

        for b in building:
            pos = self.get_block_dict_position(b)
            self.grid[pos[1]][pos[0]][pos[2]] = b
            self.pixel_grid[pos[1], pos[0], pos[2]] = 1

    def get_available_styles(self):
        """Returns a list of available styles

        :return: Formatted paragraph of available styles and their descriptions
        :rtype: str
        """
        styles = ""
        for s in self.styles["styles"].keys():
            styles += f"{s}: {self.styles['styles'][s]['description']}\n"
        return styles

    def get_styles_list(self):
        return self.styles["styles"].keys()

    def fill_empty_spaces(self):
        """Fills in empty spaces in the building with cubes
        An empty space is a region of grid spaces that do not contain any blocks
        And are surrounded by blocks on all sides and above (but not necessarily below)
        """
        label = 0
        neighbors = [
            (0, 0, 1),
            (0, 0, -1),
            (0, 1, 0),
            (0, -1, 0),
            (1, 0, 0),
            (-1, 0, 0),
        ]
        building_array = np.copy(self.pixel_grid)

        # pad outside of the building such that all empty spaces on the edges are connected
        building_array = np.pad(
            building_array,
            ((0, 1), (1, 1), (1, 1)),
            mode="constant",
            constant_values=-1,
        )
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
                                            "position": f"({i - 1}, {k}, {j - 1})",
                                        }
                                        self.pixel_grid[k, i - 1, j - 1] = 1
                                    for dy, dx, dz in neighbors:
                                        ny, nx, nz = y + dy, x + dx, z + dz
                                        if (
                                            0 <= nx < xDim
                                            and 0 <= nz < zDim
                                            and 0 <= ny < yDim
                                            and not statusArray[ny, nx, nz]
                                            and building_array[ny, nx, nz] == -1
                                        ):
                                            queue1.append((ny, nx, nz))

    def style(self, style):
        """Applies the chosen style to the building

        :param style: style to be applied
        :type style: str
        :return: building after applying the style
        :rtype: list(dict)
        """
        # Only remove floating blocks if building is not a single block
        if self.size_x != 1 or self.size_y != 1 or self.size_z != 1:
            self.remove_floating_blocks()

        self.fill_empty_spaces()
        if style in self.styles["styles"]:
            for rule in self.styles["styles"][style]["rules"]:
                matching_positions = self.apply_kernel(rule["filter"])
                for effect in rule["effects"]:
                    for c in matching_positions:
                        placeholders = {"rotation": int(c[1])}
                        block = self.grid[c[0][0]][c[0][1]][c[0][2]]
                        block[effect["key"]] = effect["value"].format_map(placeholders)
                        if block[effect["key"]].isdigit():
                            block[effect["key"]] = int(block[effect["key"]])
            return self.grid_to_json()
        else:
            return self.grid_to_json()

    def remove_floating_blocks(self):
        """Removes floating blocks from the building
        A floating block is a block that is not supported by any other block"""
        # TODO: edge case where building is a single block deletes building
        # TODO: there may be multiple floating blocks together, which are not being removed

        # Remove blocks that are not supported by any other block
        floating_block_kernel = [
            [[0, 0, 0], [0, -1, 0], [0, 0, 0]],
            [[0, -1, 0], [-1, 1, -1], [0, -1, 0]],
            [[0, 0, 0], [0, -1, 0], [0, 0, 0]],
        ]
        matching_positions = self.apply_kernel(floating_block_kernel)
        for c in matching_positions:
            self.grid[c[0][0]][c[0][1]][c[0][2]] = None
            self.pixel_grid[c[0][0], c[0][1], c[0][2]] = -1

    def grid_to_json(self):
        """Converts the grid to a list of blocks, the common format for buildings

        :return: list of blocks
        :rtype: list(dict)
        """
        json = []
        for yz in self.grid:
            for z in yz:
                for b in z:
                    if b is not None:
                        json.append(b)
        return json

    def apply_kernel(self, filter_matrix):
        """Applies a filter to the building grid
        A filter is a matrix of values 0, 1 or -1
        0: Any value
        1: Matches against a block
        -1: Matches against an empty space

        :param filter_matrix: filter to be applied
        :type filter_matrix: list(list(int) or list(list(list(int))))
        :return: matches found in the building grid
        :rtype: tuple((y, x, z), rotation)
        """

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
                                    ny, nx, nz = (
                                        y + fh - height_offset,
                                        x + fw - width_offset,
                                        z + fd - depth_offset,
                                    )
                                    # Check bounds
                                    if (
                                        0 <= ny < self.size_y
                                        and 0 <= nx < self.size_x
                                        and 0 <= nz < self.size_z
                                    ):
                                        value = self.pixel_grid[ny][nx][nz]
                                    else:
                                        value = (
                                            -1
                                        )  # Outside bounds, treat as empty space

                                    if (
                                        rotated_filter[fh][fd][fw] != 0
                                        and rotated_filter[fh][fd][fw] != value
                                    ):
                                        applies = False
                                        break
                                if not applies:
                                    break
                            if not applies:
                                break

                        if applies:
                            filtered_values.append(((y, x, z), orientation))
                            break  # only first orientation matches

        return filtered_values

    def get_block_dict_position(self, block):
        """Returns the position of a block in the grid, in the format (x, y, z)"""
        position = block["position"].replace("(", "").replace(")", "").split(",")
        return [eval(x) for x in position]

    def clean_add_ons(self):
        def is_valid_add_on(x, y , z, add_on_pos):
            ny, nx, nz = (
                add_on_pos[1],
                add_on_pos[0],
                add_on_pos[2],
            )
            dx, dy, dz = nx - x, ny - y, nz - z

            # Must be adjacent to attached block
            distance = abs(dx) + abs(dy) + abs(dz)
            if distance != 1:
                return False

            # Must be attached to a block
            if self.grid[y][x][z] is None:
                return False

            # If is outside grid size it is on an empty space
            if (
                ny < 0
                or ny >= self.size_y
                or nx < 0
                or nx >= self.size_x
                or nz < 0
                or nz >= self.size_z
            ):
                return True

            # Must be placed on an empty space
            if self.grid[ny][nx][nz] is not None:
                return False
            return True

        for y in range(self.size_y):
            for x in range(self.size_x):
                for z in range(self.size_z):
                    if self.grid[y][x][z] is not None:
                        if "tags" in self.grid[y][x][z]:
                            add_on_pos = self.get_block_dict_position(
                                self.grid[y][x][z]["tags"]
                            )

                            if not is_valid_add_on(x, y, z, add_on_pos):
                                # Place add on adjacent to the block
                                tag = self.grid[y][x][z]["tags"]
                                del self.grid[y][x][z]["tags"]
                                ny, nx, nz = (
                                    y,
                                    add_on_pos[0],
                                    add_on_pos[2],
                                )

                                dx, dz = nx - x, nz - z
                                if abs(dx) > abs(dz):
                                    dx = dx / abs(dx)  #normalize but keep direction
                                    dz = 0
                                else:
                                    dz = dz / abs(dz)  #normalize but keep direction
                                    dx = 0

                                i = 1
                                while True:
                                    if self.grid[y][x][z] is None:
                                        break
                                    nx, nz = int(x + dx * i), int(z + dz * i)
                                    if is_valid_add_on(x, y, z, (nx, ny, nz)):
                                        if "tags" not in self.grid[y][x][z]:
                                            tag["position"] = f"({nx},{ny},{nz})"
                                            self.grid[y][x][z]["tags"] = tag
                                            break
                                        else:
                                            break # There already is an addo-n
                                    x, z = nx, nz


                                # Verify if new position is valid
                                # Adjust until it is valid or until it is deemed impossible

        return
