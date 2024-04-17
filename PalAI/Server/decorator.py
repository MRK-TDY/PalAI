import numpy as np
import json
import os
import random
from functools import reduce
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
            [[[] for _ in range(self.size_z)] for _ in range(self.size_x)]
            for _ in range(self.size_y)
        ]
        self.pixel_grid = (
            np.ones((self.size_y, self.size_x, self.size_z), dtype=int) * -1
        )

        for b in self.floor_list:
            pos = self.get_block_dict_position(b)
            self.grid[pos[0]][pos[1]][pos[2]].append(b)
            self.pixel_grid[pos[0], pos[1], pos[2]] = 1

        # Remove blocks on top of existing blocks, we are only interested in floors
        to_remove = []
        for b in self.floor_list:
            pos = self.get_block_dict_position(b)
            for y in range(pos[0] + 1, self.size_y):
                if len(self.grid[y][pos[1]][pos[2]]) > 0:
                    extra = self.grid[y][pos[1]][pos[2]]
                    self.grid[y][pos[1]][pos[2]] = []
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

    def _is_valid_option(self, decoration, block, current_floor_list):
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
                # There is a wall if there is no block on the position
                # (walls are boundaries of the building)
                valid = True
                for neighbor in self.grid[new_pos[0]][new_pos[1]][new_pos[2]]:
                    if "type" in neighbor:
                        valid = False
                return valid

            elif r == "EMPTY":
                # There is an empty space if there is a block but nothing else
                if (
                    len(self.grid[new_pos[0]][new_pos[1]][new_pos[2]]) != 1
                    or "type" not in self.grid[new_pos[0]][new_pos[1]][new_pos[2]][0]
                ):
                    return False
            else:  # Adjacency to another decoration
                valid = False
                for floor in current_floor_list:
                    if list(self.get_block_dict_position(floor)) == list(new_pos):
                        for o in floor["options"]:
                            if o["name"] == r:
                                valid = True
                return valid

        return True

    def decorate(self):
        """Creates the list of decorations based on the imported building

        :return: list of decorations to be placed
        :rtype: list(dict)
        """
        # TODO: foreach level of subdivisions

        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        placed_decor = []
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
                    if not self._is_valid_option(o, b, current_floor):
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
                if len(min_entropy_block["options"]) == 0:
                    continue
                choice = random.choice(min_entropy_block["options"])
                c = {
                    "type": choice["name"],
                    "rotation": choice["rotation"],
                    "position": min_entropy_block["position"],
                }

                if c["type"] != "EMPTY":
                    placed_decor.append(c)

                # Recursively apply callbacks
                callbacker = choice
                base_position = min_entropy_block["position"]
                while callbacker.get("callback", None) is not None:
                    if random.random() > callbacker.get("callback_chance", 1):
                        break
                    base_position = (
                        base_position.replace("(", "").replace(")", "").split(",")
                    )
                    base_position[1] = eval(base_position[1]) + callbacker.get(
                        "height", 0
                    )
                    base_position = (
                        f"({base_position[0]},{base_position[1]},{base_position[2]})"
                    )
                    total_weight = reduce(
                        lambda x, y: x + y.get("weight", 1), callbacker["callback"], 0
                    )
                    rand = random.random() * total_weight
                    for option in callbacker["callback"]:
                        if rand < option["weight"]:
                            chosen = [
                                i
                                for i in self.decorations
                                if i["name"] == option["name"]
                            ][0]
                            break
                        rand -= option["weight"]

                    if chosen.get("limit", 0) != 0:
                        if used_decorations_count[chosen["name"]] >= chosen["limit"]:
                            break

                        used_decorations_count[chosen["name"]] += 1

                        if chosen["name"] != "EMPTY":
                            d = {
                                "type": chosen["name"],
                                "rotation": chosen["rotation"],
                                "position": base_position,  # + chosen.get("height", 0),
                            }
                            placed_decor.append(d)
                            pos = self.get_block_dict_position(d)
                            pos[0] = int(pos[0])

                    callbacker = chosen

                # Check limit and remove options from other blocks if reached
                if choice["limit"] > 0:
                    used_decorations_count[choice["name"]] += 1
                    if used_decorations_count[choice["name"]] >= choice["limit"]:
                        for b in current_floor:
                            b["options"] = [
                                o for o in b["options"] if o["name"] != choice["name"]
                            ]

                # Update options of neighbors based on this choice
                for i, r in enumerate(choice["adjacency"]):
                    new_pos = (
                        y,
                        self.get_block_dict_position(min_entropy_block)[1]
                        + directions[i][0],
                        self.get_block_dict_position(min_entropy_block)[2]
                        + directions[i][1],
                    )
                    if r == "EMPTY":
                        for neighbor in self.grid[new_pos[0]][new_pos[1]][new_pos[2]]:
                            neighbor["options"] = [
                                o for o in neighbor["options"] if o["name"] == "EMPTY"
                            ]
                    elif r == "WALL":
                        pass
                    elif r == "":
                        pass
                    else:
                        for neighbor in self.grid[new_pos[0]][new_pos[1]][new_pos[2]]:
                            neighbor["options"] = [
                                copy.copy(o)
                                for o in self.decorations
                                if o["name"] == r
                            ]

                # Update the neighbor options based on their own adjacency rules
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

                    for neighbor in self.grid[new_pos[0]][new_pos[1]][new_pos[2]]:
                        if "options" in neighbor:
                            neighbor["options"] = [
                                o
                                for o in neighbor["options"]
                                if self._is_valid_option(o, neighbor, current_floor)
                            ]


            return placed_decor
