import random
import re
from PalAI.Server.placeable import Placeable

directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]


def create_doors(building: list[Placeable]) -> list[Placeable]:
    """Creates doors in the building

    :param building: the building to add the doors to
    :type building: list(Placeable)
    :return: list of blocks that have been added doors
    """

    offset_x = min(building, key=lambda b: b.x).x
    offset_z = min(building, key=lambda b: b.z).z
    size_x = max(building, key=lambda b: b.x).x + 1 - offset_x
    size_z = max(building, key=lambda b: b.z).z + 1 - offset_z

    # Grid is indexed (x, z)
    grid = [[None for _ in range(size_z)] for _ in range(size_x)]

    for b in building:
        if b.y != 0 or b.block_type != "CUBE":
            continue
        grid[b.x - offset_x][b.z - offset_z] = b

    # stores only the blocks that can have doors, organized by layer, then by direction of door
    candidates = [[] for _ in range(4)]
    for x in range(size_x):
        for z in range(size_z):
            cell = grid[x][z]
            if cell is not None and cell.block_type == "CUBE":
                for i, d in enumerate(directions):
                    # a block can have a door if the block in the direction of the door is None
                    if (
                        x + d[0] < 0
                        or x + d[0] >= size_x
                        or z + d[1] < 0
                        or z + d[1] >= size_z
                        or grid[x + d[0]][z + d[1]] is None
                    ):
                        candidates[i].append(cell)

    door_count = _decide_door_count(candidates, building)
    building = _create_doors(candidates, door_count)
    return building

def _decide_door_count(candidates: list[list[Placeable]], building: list[Placeable]) -> int:
    total_candidates = sum(len(c) for c in candidates)
    ground_floor = len([b for b in building if b.y == 0])
    if ground_floor == 0 or total_candidates == 0:
        return 0

    if ground_floor > 10 and total_candidates > 10:
        return 3
    if ground_floor > 10 and total_candidates > 10:
        return 2

    return 1


def _create_doors(candidates: list[list[Placeable]], door_count: int) -> list[Placeable]:
    """Creates doors in the building

    :param candidates: list of possible candidates, organized by direction
    :return: only the placeables that have been added doors
    """
    indices = list(range(4))
    random.shuffle(indices)
    return_list = []
    for i in range(door_count):
        side = candidates[indices[i]]
        d = directions[indices[i]]
        random.shuffle(side)
        b = side[0]
        b.tags = []
        win = Placeable("DOOR", b.x + d[0], b.y, b.z + d[1])
        b.tags.append(win)
        return_list.append(b)
    return return_list
