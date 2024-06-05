import random
import numpy as np
from PalAI.Server.placeable import Placeable


def create_gardens(building: list[Placeable], rng: random.Random) -> list[Placeable]:
    """Creates the garden for a given building

    :param building: input building, will be used to determine size and placement according to doors
    :return: list of garden plots
    """

    # We need the "bounding" box of the house, as seen from above
    ground_floor = [b for b in building if b.y == 0]
    min_x = min(ground_floor, key=lambda b: b.x).x
    max_x = max(ground_floor, key=lambda b: b.x).x
    min_z = min(ground_floor, key=lambda b: b.z).z
    max_z = max(ground_floor, key=lambda b: b.z).z

    directions = ((1, 0), (0, 1), (-1, 0), (0, -1))
    chosen_rotation = rng.choice(directions)

    garden_area = _choose_garden_area(((min_x, min_z), (max_x, max_z)), chosen_rotation)
    garden_size = (
        abs(garden_area[1][0] - garden_area[0][0]),
        abs(garden_area[1][1] - garden_area[0][1]),
    )
    garden = []
    for x in range(garden_area[0][0], garden_area[1][0] + 1):
        for z in range(garden_area[0][1], garden_area[1][1] + 1):
            garden.append(Placeable(Placeable.BlockType.SMALL_GARDEN, x, 0, z))

    # Removes gardens in front of the door
    for b in building:
        if b.tags is not None and len(b.tags) > 0:
            for t in b.tags:
                t: Placeable
                if t.block_type == Placeable.BlockType.DOOR:
                    d = (t.x - b.x, t.z - b.z)
                    # there is a better data structure for this, but this is fine for now
                    for k in range(max(garden_size)):
                        for g in garden:
                            if g.x == t.x + d[0] * k and g.z == t.z + d[1] * k:
                                garden.remove(g)

    # Join gardens together
    garden_array = np.empty((garden_size[0] + 1, garden_size[1] + 1), dtype=Placeable)
    for g in garden:
        garden_array[g.x - garden_area[0][0], g.z - garden_area[0][1]] = g


    # Garden size is 1 smaller than the number of gardens
    if garden_size[0] >= 3 and garden_size[1] >= 3:
        create_4x4_garden(garden_size, garden_array, rng)
    elif garden_size[0] >= 2 and garden_size[1] >= 2:
        create_3x3_garden(garden_size, garden_array, rng)
    else:
        create_generic_garden(garden_size, garden_array, rng)

    garden = []
    for x in range(garden_size[0] + 1):
        for z in range(garden_size[1] + 1):
            if garden_array[x, z] is not None:
                garden.append(garden_array[x, z])
    return garden

def create_generic_garden(garden_size, garden_array, rng: random.Random):
    if garden_array[0, 0] is not None:
        garden_array[0, 0].block_type = Placeable.BlockType.GARDEN_LIGHT
    return


def place_lights(garden_array, garden_size, limit = 0):
    placed_lights = 0
    positions = ((0, 0), (0, garden_size[1]), (garden_size[0], 0), (garden_size[0], garden_size[1]))
    for p in positions:
        if garden_array[p[0], p[1]] is not None:
            if (p[0] == 0 or p[0] == garden_size[0]) and (p[1] == 0 or p[1] == garden_size[1]):
                garden_array[p[0], p[1]].block_type = Placeable.BlockType.GARDEN_LIGHT
                placed_lights += 1
                if placed_lights == limit:
                    return


def create_3x3_garden(garden_size, garden_array, rng: random.Random):
    # Set lights first
    place_lights(garden_array, garden_size, 2)

    # Align gardens and replacewith large
    alignment = rng.choice([0, 1])
    for x in range(garden_size[0] + 1):
        for z in range(garden_size[1] + 1):
            if garden_array[x, z] is not None:
                if (x == 0 or x == garden_size[0]) and (z == 0 or z == garden_size[1]):
                    continue # This is where lights are placed
                if alignment == 0:
                    if (
                        z < garden_size[1]
                        and garden_array[x, z + 1] is not None
                        and garden_array[x, z + 1].block_type
                        == Placeable.BlockType.SMALL_GARDEN
                    ):
                        garden_array[x, z].block_type = Placeable.BlockType.LARGE_GARDEN
                        garden_array[x, z + 1] = None
                else:
                    if (
                        x < garden_size[0]
                        and garden_array[x + 1, z] is not None
                        and garden_array[x + 1, z].block_type
                        == Placeable.BlockType.SMALL_GARDEN
                    ):
                        garden_array[x, z].block_type = Placeable.BlockType.LARGE_GARDEN
                        garden_array[x, z].rotation = 3
                        garden_array[x + 1, z] = None

def create_4x4_garden(garden_size, garden_array, rng: random.Random):
    place_lights(garden_array, garden_size, 4)

    # Align gardens and replacewith large
    alignment = rng.choice([0, 1])
    for x in range(garden_size[0] + 1):
        for z in range(garden_size[1] + 1):
            if garden_array[x, z] is not None:
                if (x == 0 or x == garden_size[0]) and (z == 0 or z == garden_size[1]):
                    continue # This is where lights are placed
                if alignment == 0:
                    if (
                        z < garden_size[1]
                        and garden_array[x, z + 1] is not None
                        and garden_array[x, z + 1].block_type
                        == Placeable.BlockType.SMALL_GARDEN
                    ):
                        garden_array[x, z].block_type = Placeable.BlockType.LARGE_GARDEN
                        garden_array[x, z + 1] = None
                else:
                    if (
                        x < garden_size[0]
                        and garden_array[x + 1, z] is not None
                        and garden_array[x + 1, z].block_type
                        == Placeable.BlockType.SMALL_GARDEN
                    ):
                        garden_array[x, z].block_type = Placeable.BlockType.LARGE_GARDEN
                        garden_array[x, z].rotation = 3
                        garden_array[x + 1, z] = None


def _choose_garden_area(building_area: tuple[tuple[float]], door_rotation: tuple[int]):
    # area is calculated as such:
    # with a size of 1 the garden perfectly mirrors the house
    # direction is chosen based on the door, such that the garden is outside it
    # there is then a buffer of 1 block between the house and garden

    # Using garden size as 1 for now
    building_size_x = abs(building_area[1][0] - building_area[0][0])
    building_size_z = abs(building_area[1][1] - building_area[0][1])
    garden_size_x = min(int(building_size_x * 1), 3)
    garden_size_z = min(int(building_size_z * 1), 3)

    match (door_rotation):
        # I don't know why we add by 2 instead of 1, but it works
        case (1, 0):
            starting_point_x = building_area[0][0] + building_size_x + 2
            starting_point_z = building_area[0][1]
        case (0, 1):
            starting_point_x = building_area[0][0]
            starting_point_z = building_area[0][1] + building_size_z + 2

        # negative cases are subtracted by the garden size, as that is the offset size
        case (-1, 0):
            starting_point_x = building_area[0][0] - garden_size_x - 2
            starting_point_z = building_area[0][1]
        case (0, -1):
            starting_point_x = building_area[0][0]
            starting_point_z = building_area[0][1] - garden_size_z - 2

    end_point_x = starting_point_x + garden_size_x
    end_point_z = starting_point_z + garden_size_z

    return ((starting_point_x, starting_point_z), (end_point_x, end_point_z))
