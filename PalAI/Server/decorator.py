import copy
import json
import os
import random
from functools import reduce

import numpy as np

from PalAI.Server.Decorator.cell import Cell, CellType
from PalAI.Server.Decorator.prefab import Prefab
from PalAI.Server.placeable import Placeable


class Decorator:
    def __init__(
        self,
        rng: random.Random,
        available_decorations: list[str] = None,
        style_sheet="decorations.json",
    ):
        """

        :param style_sheet: list of decorations and their rules
        :type style_sheet: (str) relative path to the style sheet
        """
        self.rng = rng
        with open(os.path.join(os.path.dirname(__file__), style_sheet), "r") as fptr:
            loaded = json.load(fptr)

            self.decorations: list[Prefab] = []

            self.rooms = loaded["rooms"]
            self.decorations_by_room: dict[str, list[Prefab]] = {}
            for r in self.rooms:
                self.decorations_by_room[r["name"]] = []
            self.decorations_by_room["default"] = []

            for d in loaded["decorations"]:
                p = Prefab(
                    d.get("name", ""),
                    d.get("rotation", 0),
                    d.get("asset_name", d["name"]),
                    d.get("adjacency", ["", "", "", ""]),
                    d.get("limit", 0),
                )
                self.decorations.append(p)

                room = d.get("room", "default")
                self.decorations_by_room[room].append(p)

            if available_decorations is not None and available_decorations != []:
                # Filter self.decorations to only include those whose asset_name contains any of the given decorations
                self.decorations = [
                    d
                    for d in self.decorations
                    if any(
                        decoration in d.asset_names + [d.name]
                        for decoration in available_decorations
                    )
                ]

        rotated_decorations = []
        for d in self.decorations:
            # Rotations
            seen_adjacencies = [d.adjacency_rules]
            for i in range(1, 4):
                new_adjacency = [seen_adjacencies[-1][-1]] + seen_adjacencies[-1][:-1]
                if new_adjacency not in seen_adjacencies:
                    aux = copy.deepcopy(d)
                    aux.adjacency_rules = new_adjacency
                    aux.rotation = i
                    rotated_decorations.append(aux)
                    seen_adjacencies.append(new_adjacency)

        self.decorations += rotated_decorations

        self.directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

    def import_building(self, api_building: list[Placeable]):
        """Imports the building from the API response and creates the necessary data structures"""
        blocks = copy.deepcopy(api_building)
        self.floor_list: list[Cell] = []
        for b in blocks:
            if b.y == 0:
                ct = (
                    CellType.INVALID
                    if b.has_door() or b.block_type != Placeable.BlockType.CUBE
                    else CellType.VALID
                )
                self.floor_list.append(Cell(b.x, b.z, ct, self.decorations.copy()))

        if not self.floor_list:
            return

        self.offset_x = min(self.floor_list, key=lambda b: b.x).x
        self.offset_z = min(self.floor_list, key=lambda b: b.z).z
        self.size_x = max(self.floor_list, key=lambda b: b.x).x + 1 - self.offset_x
        self.size_z = max(self.floor_list, key=lambda b: b.z).z + 1 - self.offset_z

        # Grid is indexed (x, z) because most transformations happen on a slice of the y axis
        self.grid: list[list[list[Cell]]] = [
            [[] for _ in range(self.size_z)] for _ in range(self.size_x)
        ]
        self.pixel_grid: np.ndarray = (
            np.ones((self.size_x, self.size_z), dtype=int) * -1
        )

        for b in self.floor_list:
            self.grid[b.x - self.offset_x][b.z - self.offset_z].append(b)
            self.pixel_grid[b.x - self.offset_x, b.z - self.offset_z] = 1

        # Apply rooms
        if self.floor_list:
            for r in self.rooms:
                seed = self.rng.choice(self.floor_list)

                for b in sorted(self.floor_list, key=lambda _: self.rng.random()):
                    if len(self._get_pos_neighbors(b.x, b.z)) < 4:
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
                    seed.possibilities = self.decorations_by_room[r["name"]].copy()

                    closed.append(seed)
                    for b in self._get_pos_neighbors(b.x, b.z):
                        if b not in open and b not in closed:
                            open.append(b)

    def decorate(self):
        """Creates the list of decorations based on the imported building

        :return: list of decorations to be placed
        :rtype: list(dict)
        """

        if not self.floor_list:
            # sometimes there are only diagonals or other blocks on the ground floor
            return []

        placed_decors = []
        self.used_decorations_count = {
            d.name: 0 for d in self.decorations if d.limit > 0
        }

        for b in self.floor_list:
            to_remove = []
            for o in b.possibilities:
                if not self._is_valid_option(b, o):
                    to_remove.append(o)
            for r in to_remove:
                b.possibilities.remove(r)

        while len(self.floor_list) > 0:
            # Unlike regular WFC we don't choose the lowest entropy block
            # This is because of the limits, which means not all blocks will be collapsed
            # Choosing the lowest entropy would cause the blocks with less options to fill first
            current_block = sorted(self.floor_list, key=lambda _: self.rng.random())[0]
            if not any(current_block.possibilities) or current_block.collapsed:
                self.floor_list.remove(current_block)
                continue

            # Get a random decoration but prioritize least used types first
            current_block.possibilities = sorted(
                current_block.possibilities,
                key=lambda x: self.rng.random()
                - self.used_decorations_count.get(x.name, 0),
            )
            current_decor = self.rng.choice(current_block.possibilities)

            # Add the chosen decoration
            self._add_decoration(
                current_decor, current_block, placed_decors, self.floor_list
            )

            # TODO: reenable callbacks
            # Recursively apply callbacks
            # self._apply_callback(
            #     current_decor,
            #     current_block,
            #     placed_decors,
            #     self.floor_list,
            # )

            # Check limit and remove options from other blocks if reached
            self._check_limits(current_decor, self.floor_list)

            # Update options of neighbors based on this choice
            self._update_neighbors(
                current_decor, current_block, self.floor_list, placed_decors
            )

            # Update the neighbor options based on their own adjacency rules
            self._validate_cell(current_block.x, current_block.z, self.floor_list)

        return placed_decors

    def _check_limits(self, decor: Prefab, current_floor: list[Cell]):
        if decor.limit > 0:
            self.used_decorations_count[decor.name] += 1
            if self.used_decorations_count[decor.name] >= decor.limit:
                for b in current_floor:
                    b.possibilities = [
                        o for o in b.possibilities if o.name != decor.name
                    ]

    def _validate_cell(self, x, z, current_floor):
        for neighbor in self._get_pos_neighbors(x, z):
            neighbor.possibilities = [
                o for o in neighbor.possibilities if self._is_valid_option(neighbor, o)
            ]

    def _update_neighbors(
        self,
        chosen_decor: Prefab,
        chosen_block: Cell,
        current_floor: list[Cell],
        placed_decors: list[Prefab],
    ):
        for i, r in enumerate(chosen_decor.adjacency_rules):
            if r == "EMPTY":
                pass
            elif r == "WALL":
                pass
            elif r == "":
                pass
            else:
                new_x = (chosen_block.x + self.directions[i][0],)
                new_z = (chosen_block.z + self.directions[i][1],)

                placed = False
                for floor in current_floor:
                    if floor.x == new_x and floor.z == new_z:
                        for d in floor.possibilities:
                            if d.name == r:
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

        decor_type = (
            self.rng.choice(decor.asset_names)
            if len(decor.asset_names) > 0
            else decor.name
        )
        block.collapsed = True
        block.prefab = [decor]

        c = {
            "type": decor_type,
            "rotation": decor.rotation,
            "position": f"({block.x},0,{block.z})",
        }

        if c["type"] != "EMPTY":
            placed_decors.append(c)

            self._check_limits(decor, current_floor)

    def _get_pos_neighbors(self, x, z) -> list[Cell]:
        neighbors = []
        for d in self.directions:
            new_x = x + d[0]
            new_z = z + d[1]

            if (
                new_x < self.offset_x
                or new_x - self.offset_x >= self.size_x
                or new_z < self.offset_z
                or new_z - self.offset_z >= self.size_z
            ):
                continue

            for b in self.grid[new_x - self.offset_x][new_z - self.offset_z]:
                neighbors.append(b)

        return neighbors

    def _is_valid_option(self, block: Cell, decor: Prefab) -> bool:
        """Evaluates if a decoration can be placed on a block

        :param decoration: decoration to be evaluated
        :type decoration: dict
        :param block: block to place the decoration
        :type block: dict
        :return: can the decoration be placed on the block
        :rtype: bool
        """
        if block.cell_type == CellType.INVALID:
            return False

        for i, r in enumerate(decor.adjacency_rules):
            if r == "":
                continue

            nx = block.x + self.directions[i][0]
            nz = block.z + self.directions[i][1]

            # If falls outside the grid, dependency must be a wall
            if (
                nx < self.offset_x
                or nz < self.offset_z
                or nx - self.offset_x >= self.size_x
                or nz - self.offset_z >= self.size_z
            ):
                if r == "WALL":
                    continue
                else:
                    return False

            if r == "WALL":
                # There is a wall if there is no block on the position
                # (walls are boundaries of the building)
                if any(self.grid[nx - self.offset_x][nz - self.offset_z]):
                    return False
                continue

            elif r == "EMPTY":
                # There is an empty space if there is a block
                if not any(
                    b.cell_type != CellType.INVALID
                    for b in self.grid[nx - self.offset_x][nz - self.offset_z]
                ):
                    return False
            else:  # Adjacency to another decoration
                valid = False
                for floor in self.grid[nx - self.offset_x][nz - self.offset_z]:
                    hypothetical_decorations = (
                        floor.prefab if floor.collapsed else floor.possibilities
                    )
                    for p in hypothetical_decorations:
                        if p.name == r:
                            valid = True
                            break

                if not valid:
                    return False

        return True
