import numpy as np
import json
import os
import random
from functools import reduce
import copy

from numpy.core.multiarray import empty
from PalAI.Server.placeable import Placeable


class Decorator:
    def __init__(self, style_sheet="decorations.json"):
        """

        :param style_sheet: list of decorations and their rules
        :type style_sheet: (str) relative path to the style sheet
        """
        with open(os.path.join(os.path.dirname(__file__), style_sheet), "r") as fptr:
            loaded = json.load(fptr)
            self.decorations = loaded["decorations"]
            self.rooms = loaded["rooms"]

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
        empty_decoration = {
            "name": "EMPTY",
            "adjacency": ["", "", "", ""],
            "limit": 0,
            "rotation": 0,
        }
        self.decorations.append(empty_decoration)

        self.decorations_by_room = {}
        for r in self.rooms:
            self.decorations_by_room[r["name"]] = [empty_decoration]
        self.decorations_by_room["default"] = [empty_decoration]
        for d in self.decorations:
            room = d.get("room", "default")
            self.decorations_by_room[room].append(d)

        self.directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

    def import_building(self, api_building):
        """Imports the building from the API response and creates the necessary data structures

        :param api_building: building (or list of blocks) to be imported
        :type api_building: list(dict)
        """
        self.floor_list: list[Placeable] = copy.deepcopy(api_building)
        to_remove = []
        for b in self.floor_list:
            if b.block_type != Placeable.BlockType.CUBE:
                to_remove.append(b)
            else:
                b["options"] = self.decorations

        for i in to_remove:
            self.floor_list.remove(i)

        self.size_y = max(self.floor_list, key=lambda b: b.y).y + 1
        self.size_x = max(self.floor_list, key=lambda b: b.x).x + 1
        self.size_z = max(self.floor_list, key=lambda b: b.z).z + 1

        # Grid is indexed (y, x, z) because most transformations happen on a slice of the y axis
        self.grid = [
            [[[] for _ in range(self.size_z)] for _ in range(self.size_x)]
            for _ in range(self.size_y)
        ]
        self.pixel_grid = (
            np.ones((self.size_y, self.size_x, self.size_z), dtype=int) * -1
        )

        for b in self.floor_list:
            self.grid[b.y][b.x][b.z].append(b)
            self.pixel_grid[b.y, b.x, b.z] = 1

        # Remove blocks on top of existing blocks, we are only interested in floors
        to_remove = []
        for b in self.floor_list:
            for y in range(b.y + 1, self.size_y):
                if len(self.grid[y][b.x][b.z]) > 0:
                    extra = self.grid[y][b.x][b.z]
                    self.grid[y][b.x][b.z] = []
                    self.pixel_grid[y][b.x][b.z] = -1
                    if b not in to_remove:
                        to_remove.append(extra)
                else:
                    break  # If there is an empty space above a block there may be another floor above

        for i in to_remove:
            if i in self.floor_list:
                self.floor_list.remove(i)

        # Apply rooms
        for r in self.rooms:
            seed = random.choice(self.floor_list)

            for b in sorted(self.floor_list, key=lambda _: random.random()):
                if len(self._get_pos_neighbors((b.y, b.x, b.z))) < 4:
                    seed = b
                    break

            open, closed = [], []
            open.append(seed)
            i = 0
            while (
                i < int(float(r["coverage"]) * len(self.floor_list))
                and len(open) > 0
                and len(closed) < len(self.floor_list)
            ):
                i += 1
                seed = open.pop(0)
                seed["room"] = r["name"]
                closed.append(seed)
                for b in self._get_pos_neighbors((b.y, b.x, b.z)):
                    if b not in open and b not in closed:
                        open.append(b)

        # Recalculate size_y
        self.size_y = max(self.floor_list, key=lambda b: b.y).y + 1

    def _is_valid_option(self, decoration, block, current_floor_list):
        """Evaluates if a decoration can be placed on a block

        :param decoration: decoration to be evaluated
        :type decoration: dict
        :param block: block to place the decoration
        :type block: dict
        :return: can the decoration be placed on the block
        :rtype: bool
        """
        for i, r in enumerate(decoration["adjacency"]):
            if r == "":
                continue

            ny = block.y
            nx = block.x + self.directions[i][0]
            nz = block.z + self.directions[i][1]

            if (
                ny < 0
                or nx < 0
                or nz < 0
                or ny >= self.size_y
                or nx >= self.size_x
                or nz >= self.size_z
            ):
                if r == "WALL":
                    continue
                else:
                    return False

            if r == "WALL":
                # There is a wall if there is no block on the position
                # (walls are boundaries of the building)
                valid = True
                for neighbor in self.grid[ny][nx][nz]:
                    if neighbor.block_type == Placeable.BlockType.CUBE:
                        valid = False
                return valid

            elif r == "EMPTY":
                # There is an empty space if there is a block
                if (
                    len(self.grid[ny][nx][nz]) < 1
                    or self.grid[ny][nx][nz][0].block_type != Placeable.BlockType.CUBE
                ):
                    return False
            else:  # Adjacency to another decoration
                valid = False
                for floor in current_floor_list:
                    if block.y == ny and block.x == nx and block.z == nz:
                        if "name" in floor._additional_keys and floor._additional_keys["name"] == r:
                            valid = True
                            break
                        if "options"._additional_keys in floor:
                            for o in floor["options"]._additional_keys:
                                if o["name"]._additional_keys == r:
                                    valid = True
                                    break
                return valid

        return True

    def decorate(self):
        """Creates the list of decorations based on the imported building

        :return: list of decorations to be placed
        :rtype: list(dict)
        """
        # TODO: foreach level of subdivisions

        placed_decors = []
        used_decorations_count = {
            d["name"]: 0 for d in self.decorations if d["limit"] > 0
        }

        # foreach floor level
        for y in range(self.size_y):
            # Initialize options for each block
            current_floor = [b for b in self.floor_list if b.y == y]
            for b in current_floor:
                if "room" in b._additional_keys:
                    b["options"] = self.decorations_by_room[b["room"]].copy()
                else:
                    b["options"] = self.decorations_by_room["default"].copy()
                to_remove = []
                for o in b["options"]:
                    if not self._is_valid_option(o, b, current_floor):
                        to_remove.append(o)

                for o in to_remove:
                    b["options"].remove(o)

            while len(current_floor) > 0:
                # Unlike regular WFC we don't choose the lowest entropy block
                # This is because of the limits, which means not all blocks will be collapsed
                # Choosing the lowest entropy would cause the blocks with less options to fill first
                current_block = sorted(current_floor, key=lambda _: random.random())[0]
                if len(current_block["options"]) == 0:
                    current_floor.remove(current_block)
                    continue

                # Get a random decoration but prioritize least used types first
                current_block["options"] = sorted(
                    current_block["options"],
                    key=lambda x: random.random()
                    - used_decorations_count.get(x["name"], 0),
                )
                current_decor = random.choice(current_block["options"])

                # Add the chosen decoration
                self._add_decoration(
                    current_decor, current_block, placed_decors, current_floor
                )

                # Recursively apply callbacks
                self._apply_callback(
                    current_decor,
                    used_decorations_count,
                    current_block,
                    placed_decors,
                    current_floor,
                )

                # Check limit and remove options from other blocks if reached
                self._check_limits(current_decor, used_decorations_count, current_floor)

                # Update options of neighbors based on this choice
                self._update_neighbors(
                    current_decor, current_block, current_floor, placed_decors
                )

                # Update the neighbor options based on their own adjacency rules
                self._validate_cell((current_block.y, current_block.x, current_block.z), current_floor)

            return placed_decors

    def _apply_callback(
        self,
        current_decoration,
        used_decorations_count,
        current_block,
        placed_decors,
        current_floor,
    ):
        callbacker = current_decoration
        while callbacker.get("callback", None) is not None:
            if random.random() > callbacker.get("callback_chance", 1):
                break
            total_weight = reduce(
                lambda x, y: x + y.get("weight", 1), callbacker["callback"], 0
            )
            rand = random.random() * total_weight
            for option in callbacker["callback"]:
                if rand < option["weight"]:
                    chosen = [
                        i for i in self.decorations if i["name"] == option["name"]
                    ][0]
                    break
                rand -= option["weight"]

            if chosen.get("limit", 0) != 0:
                if used_decorations_count[chosen["name"]] >= chosen["limit"]:
                    break

                used_decorations_count[chosen["name"]] += 1

                if chosen["name"] != "EMPTY":
                    self._add_decoration(
                        chosen, current_block, placed_decors, current_floor
                    )

            callbacker = chosen

    def _check_limits(self, decor, used_decorations_count, current_floor):
        if decor["limit"] > 0:
            used_decorations_count[decor["name"]] += 1
            if used_decorations_count[decor["name"]] >= decor["limit"]:
                for b in current_floor:
                    b["options"] = [
                        o for o in b["options"] if o["name"] != decor["name"]
                    ]

    def _validate_cell(self, pos, current_floor):
        for neighbor in self._get_pos_neighbors(pos):
            if "options" in neighbor:
                neighbor["options"] = [
                    o
                    for o in neighbor["options"]
                    if self._is_valid_option(o, neighbor, current_floor)
                ]

    def _update_neighbors(
        self, chosen_decor, chosen_block, current_floor, placed_decors
    ):
        for i, r in enumerate(chosen_decor["adjacency"]):
            new_pos = (
                chosen_block.y,
                chosen_block.x + self.directions[i][0],
                chosen_block.z + self.directions[i][1],
            )
            if r == "EMPTY":
                pass
            elif r == "WALL":
                pass
            elif r == "":
                pass
            else:
                placed = False
                for floor in current_floor:
                    if floor.x == chosen_block.x and floor.y == chosen_block.y and floor.z == chosen_block.z:
                        if "options" in floor:
                            for d in floor["options"]:
                                if d["name"] == r:
                                    self._add_decoration(
                                        d, floor, placed_decors, current_floor
                                    )
                                    placed = True
                                    break
                        if placed:
                            break

    def _add_decoration(self, decor, block, placed_decors, current_floor):
        if block in current_floor:
            current_floor.remove(block)

        decor_type = random.choice(decor.get("asset_name", [decor["name"]]))

        y = int(block.y)
        c = {
            "type": decor_type,
            "rotation": decor["rotation"],
            "position": block.position,
        }

        if c["type"] != "EMPTY":
            placed_decors.append(c)
            self.grid[y][block.x][block.z].append(c)

    def _get_pos_neighbors(self, pos):
        neighbors = []
        for d in self.directions:
            new_pos = (pos[0], pos[1] + d[0], pos[2] + d[1])

            if (
                new_pos[0] < 0
                or new_pos[1] < 0
                or new_pos[2] < 0
                or new_pos[0] >= self.size_y
                or new_pos[1] >= self.size_x
                or new_pos[2] >= self.size_z
            ):
                continue

            for b in self.grid[new_pos[0]][new_pos[1]][new_pos[2]]:
                neighbors.append(b)

        return neighbors
