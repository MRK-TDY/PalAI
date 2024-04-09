import numpy as np
import json
import os
import random
import copy


class Decorator:
    def __init__(self, style_sheet="decorations.json"):
        """

        :param style_sheet: list of decorations and their rules
        :type style_sheet: (str) relative path to the style sheet
        """
        with open(os.path.join(os.path.dirname(__file__), style_sheet), "r") as fptr:
            self.decorations = json.load(fptr)["decorations"]

        rotated_decorations = []
        for d in self.decorations:
            if "adjacency" not in d:
                d["adjacency"] = ["", "", "", ""]
            if "limit" not in d:
                d["limit"] = 0
            if "rotation" not in d:
                d["rotation"] = 0

            # Rotations
            adjacency = d["adjacency"]
            for i in range(1, 4):
                new_adjacency = [adjacency[-1]] + adjacency[:-1]
                if new_adjacency != adjacency:
                    aux = copy.deepcopy(d)
                    aux["adjacency"] = new_adjacency
                    aux["rotation"] = i
                    rotated_decorations.append(aux)
                adjacency = new_adjacency

        self.decorations += rotated_decorations
        self.decorations.append(
            {"name": "EMPTY", "adjacency": ["", "", "", ""], "limit": 0, "rotation": 0}
        )

    def import_building(self, api_building):
        """Imports the building from the API response and creates the necessary data structures

        :param api_building: building (or list of blocks) to be imported
        :type api_building: list(dict)
        """
        self.floor_list = copy.deepcopy(api_building)
        to_remove = []
        for b in self.floor_list:
            if b["type"] != "CUBE":
                to_remove.append(b)
            else:
                b["type"] = "FLOOR"
                b["options"] = self.decorations

        for i in to_remove:
            self.floor_list.remove(i)

        positions = [self.get_block_dict_position(b) for b in self.floor_list]

        self.size_y = max(positions, key=lambda x: x[0])[0] + 1
        self.size_x = max(positions, key=lambda x: x[1])[1] + 1
        self.size_z = max(positions, key=lambda x: x[2])[2] + 1

        # Grid is indexed (y, x, z) because most transformations happen on a slice of the y axis
        self.grid = [
            [[None for _ in range(self.size_z)] for _ in range(self.size_x)]
            for _ in range(self.size_y)
        ]
        self.pixel_grid = (
            np.ones((self.size_y, self.size_x, self.size_z), dtype=int) * -1
        )

        for b in self.floor_list:
            pos = self.get_block_dict_position(b)
            self.grid[pos[0]][pos[1]][pos[2]] = b
            self.pixel_grid[pos[0], pos[1], pos[2]] = 1

        # Remove blocks on top of existing blocks, we are only interested in floors
        to_remove = []
        for b in self.floor_list:
            pos = self.get_block_dict_position(b)
            for y in range(pos[0] + 1, self.size_y):
                if self.grid[y][pos[1]][pos[2]] is not None:
                    extra = self.grid[y][pos[1]][pos[2]]
                    self.grid[y][pos[1]][pos[2]] = None
                    self.pixel_grid[y][pos[1]][pos[2]] = -1
                    if b not in to_remove:
                        to_remove.append(extra)
                else:
                    break  # If there is an empty space above a block there may be another floor above

        for i in to_remove:
            self.floor_list.remove(i)

        # Recalculate size_y
        positions = [self.get_block_dict_position(b) for b in self.floor_list]
        self.size_y = max(positions, key=lambda x: x[0])[0] + 1

    def get_block_dict_position(self, block):
        """Returns the position of a block in the grid, in the format (y, x, z)"""
        position = block["position"].replace("(", "").replace(")", "").split(",")
        position[0], position[1] = position[1], position[0]
        return [eval(x) for x in position]

    def _is_valid_option(self, decoration, block):
        """Evaluates if a decoration can be placed on a block

        :param decoration: decoration to be evaluated
        :type decoration: dict
        :param block: block to place the decoration
        :type block: dict
        :return: can the decoration be placed on the block
        :rtype: bool
        """
        pos = self.get_block_dict_position(block)
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        for i, r in enumerate(decoration["adjacency"]):
            if r == "":
                continue

            new_pos = (pos[0], pos[1] + directions[i][0], pos[2] + directions[i][1])

            if (
                new_pos[0] < 0
                or new_pos[1] < 0
                or new_pos[2] < 0
                or new_pos[0] >= self.size_y
                or new_pos[1] >= self.size_x
                or new_pos[2] >= self.size_z
            ):
                if r == "WALL":
                    continue
                else:
                    return False

            if r == "WALL":
                neighbor = self.grid[new_pos[0]][new_pos[1]][new_pos[2]]
                if neighbor is not None:
                    return False

            elif r == "EMPTY":
                neighbor = self.grid[new_pos[0]][new_pos[1]][new_pos[2]]
                if neighbor is None:
                    return False
            else:
                return False  # TODO: implement adjacency with other decorations

        return True

    def decorate(self):
        """Creates the list of decorations based on the imported building

        :return: list of decorations to be placed
        :rtype: list(dict)
        """
        # TODO: foreach level of subdivisions

        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        collapsed = []
        used_decorations_count = {
            d["name"]: 0 for d in self.decorations if d["limit"] > 0
        }

        # foreach floor level
        for y in range(self.size_y):
            # Initialize options for each block
            current_floor = [
                b for b in self.floor_list if self.get_block_dict_position(b)[0] == y
            ]
            for b in current_floor:
                b["options"] = self.decorations.copy()
                to_remove = []
                for o in b["options"]:
                    if not self._is_valid_option(o, b):
                        to_remove.append(o)

                for o in to_remove:
                    b["options"].remove(o)

            # Pick the block with the smallest entropy
            while len(current_floor) > 0:

                # Collapse minimum entropy block
                min_entropy_block = sorted(
                    current_floor, key=lambda x: len(x["options"]) + random.random()
                )[0]
                current_floor.remove(min_entropy_block)
                choice = random.choice(min_entropy_block["options"])
                c = {
                    "type": choice["name"],
                    "rotation": choice["rotation"],
                    "position": min_entropy_block["position"],
                }

                if choice["limit"] > 0:
                    used_decorations_count[choice["name"]] += 1
                    if used_decorations_count[choice["name"]] >= choice["limit"]:
                        for b in current_floor:
                            b["options"] = [
                                o for o in b["options"] if o["name"] != choice["name"]
                            ]

                for i, r in enumerate(choice["adjacency"]):
                    if r == "EMPTY":
                        new_pos = (
                            y,
                            self.get_block_dict_position(min_entropy_block)[1]
                            + directions[i][0],
                            self.get_block_dict_position(min_entropy_block)[2]
                            + directions[i][1],
                        )
                        neighbor = self.grid[new_pos[0]][new_pos[1]][new_pos[2]]
                        if neighbor is not None:
                            neighbor["options"] = [
                                o for o in neighbor["options"] if o["name"] == "EMPTY"
                            ]

                if c["type"] != "EMPTY":
                    collapsed.append(c)

                for i, d in enumerate(directions):
                    pos = self.get_block_dict_position(c)
                    new_pos = (pos[0], pos[1] + d[0], pos[2] + d[1])

                    # TODO: collapse other blocks based on option chosen
                    if (
                        new_pos[0] < 0
                        or new_pos[1] < 0
                        or new_pos[2] < 0
                        or new_pos[0] >= self.size_y
                        or new_pos[1] >= self.size_x
                        or new_pos[2] >= self.size_z
                    ):
                        continue

                    # Update options of all neighbors
                    neighbor = self.grid[new_pos[0]][new_pos[1]][new_pos[2]]
                    if neighbor is not None:
                        neighbor["options"] = [
                            o
                            for o in neighbor["options"]
                            if self._is_valid_option(o, neighbor)
                        ]

            return collapsed
