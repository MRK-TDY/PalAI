import os
import numpy as np
import json
from collections import deque

from PalAI.Server.placeable import Placeable


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

        self.offset_x = min(building, key=lambda b: b.x).x
        self.offset_y = min(building, key=lambda b: b.y).y
        self.offset_z = min(building, key=lambda b: b.z).z
        self.size_x = max(building, key=lambda b: b.x).x + 1 - self.offset_x
        self.size_y = max(building, key=lambda b: b.y).y + 1 - self.offset_y
        self.size_z = max(building, key=lambda b: b.z).z + 1 - self.offset_z

        # Grid is indexed (y, x, z) because most transformations happen on a slice of the y axis
        self.grid = [
            [[None for _ in range(self.size_z)] for _ in range(self.size_x)]
            for _ in range(self.size_y)
        ]
        self.pixel_grid = (
            np.ones((self.size_y, self.size_x, self.size_z), dtype=int) * -1
        )

        for b in building:
            self.grid[b.y - self.offset_y][b.x - self.offset_x][b.z - self.offset_z] = b
            self.pixel_grid[
                b.y - self.offset_y, b.x - self.offset_x, b.z - self.offset_z
            ] = 1

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
        return [i.upper() for i in self.styles["styles"].keys()]

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
                                        p = Placeable(
                                            "CUBE",
                                            i - 1 + self.offset_x,
                                            k + self.offset_y,
                                            j - 1 + self.offset_z,
                                        )
                                        self.grid[k][i - 1][j - 1] = p
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
        for s in self.styles["styles"]:
            if s.upper() == style.upper():
                for rule in self.styles["styles"][s]["rules"]:
                    matching_positions = self.apply_kernel(rule["filter"])
                    for effect in rule["effects"]:
                        for c in matching_positions:
                            placeholders = {"rotation": int(c[1])}
                            block = self.grid[c[0][0]][c[0][1]][c[0][2]]
                            block[effect["key"]] = effect["value"].format_map(
                                placeholders
                            )
                            if (
                                not isinstance(block[effect["key"]], int)
                                and block[effect["key"]].isdigit()
                            ):
                                block[effect["key"]] = int(block[effect["key"]])
                break
        else:
            raise ValueError(f"Style {style} not found")
        self.remove_impossible_add_ons()
        return self.export_building()

    def remove_floating_blocks(self):
        """Removes floating blocks from the building
        A floating block is a block that is not supported by any other block"""
        # TODO: there may be multiple floating blocks together, which are not being removed

        # Remove blocks that are not supported by any other block
        floating_block_kernel = [
            [[0, 0, 0], [0, -1, 0], [0, 0, 0]],
            [[0, -1, 0], [-1, 1, -1], [0, -1, 0]],
            [[0, 0, 0], [0, -1, 0], [0, 0, 0]],
        ]
        matching_positions = self.apply_kernel(floating_block_kernel)
        block_count = len(self.export_building())

        for c in matching_positions:
            if block_count <= 1:
                break
            if c[0][0] == 0:
                continue  #allow floating blocks on the ground floor
            block_count -= 1
            self.grid[c[0][0]][c[0][1]][c[0][2]] = None
            self.pixel_grid[c[0][0], c[0][1], c[0][2]] = -1

    def create_windows(self, window_styles, window_quantifiers):
        """Creates windows in the building

        :param window_styles: style of the windows
        :type window_styles: list(str)
        :param window_quantifiers: ration of windows to be created (vs total possibilities)
        :type window_quantifiers: list(float) (0 to 1)
        :return: None
        """
        for i, w in enumerate(window_styles):
            match w:
                case "maximalist":
                    pass
                case "symmetric":
                    pass
                case "erratic":
                    pass
                case "none":
                    pass
                case _:
                    pass
        return

    def export_building(self):
        """Converts the grid to a list of blocks, the common format for buildings

        :return: list of blocks
        :rtype: list(Placeable)
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

    def remove_impossible_add_ons(self):
        for y in range(self.size_y):
            for x in range(self.size_x):
                for z in range(self.size_z):
                    block: Placeable = self.grid[y][x][z]
                    if block is not None and block.block_type != "CUBE" and len(block.tags) > 0:
                        block.tags = []

