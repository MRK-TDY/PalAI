import random
from PalAI.Server.placeable import Placeable

directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]


def create_windows(
    building: list[Placeable],
    window_styles: list[str],
    window_quantifiers: list[float],
    rng: random.Random,
) -> list[Placeable]:
    """Creates windows in the building

    :param building: the building to add the windows to
    :type building: list(Placeable)
    :param window_styles: style of the windows
    :type window_styles: list(str)
    :param window_quantifiers: ration of windows to be created (vs total possibilities)
    :type window_quantifiers: list(float) (0 to 1)
    :return: None
    """

    offset_x = min(building, key=lambda b: b.x).x
    offset_y = min(building, key=lambda b: b.y).y
    offset_z = min(building, key=lambda b: b.z).z
    size_x = max(building, key=lambda b: b.x).x + 1 - offset_x
    size_y = max(building, key=lambda b: b.y).y + 1 - offset_y
    size_z = max(building, key=lambda b: b.z).z + 1 - offset_z

    # Grid is indexed (y, x, z) because most transformations happen on a slice of the y axis
    grid = [
        [[None for _ in range(size_z)] for _ in range(size_x)] for _ in range(size_y)
    ]

    for b in building:
        grid[b.y - offset_y][b.x - offset_x][b.z - offset_z] = b

    # stores only the blocks that can have windows, organized by layer, then by direction of window
    layered_candidates = [[[] for _ in range(4)] for _ in range(size_y)]
    for y in range(size_y):
        for x in range(size_x):
            for z in range(size_z):
                cell = grid[y][x][z]
                if cell is not None and cell.block_type == "CUBE":
                    for i, d in enumerate(directions):
                        # a block can have a window if the block in the direction of the window is None
                        if (
                            x + d[0] < 0
                            or x + d[0] >= size_x
                            or z + d[1] < 0
                            or z + d[1] >= size_z
                            or grid[y][x + d[0]][z + d[1]] is None
                        ):
                            layered_candidates[y][i].append(cell)

    for i, w in enumerate(window_styles):
        match w:
            case "maximalist":
                _create_maximalist_windows(layered_candidates[i], window_quantifiers[i], rng)
            case "symmetric":
                _create_symmetric_windows(layered_candidates[i], window_quantifiers[i], rng)
            case "default":
                _create_default_windows(layered_candidates[i], window_quantifiers[i], rng)
            case "erratic":
                _create_erratic_windows(layered_candidates[i], window_quantifiers[i], rng)
            case "none":
                pass
            case _:
                pass
    return building


def _create_erratic_windows(
    layered_candidates: list[list[Placeable]],
    window_quantifier: float,
    rng: random.Random,
):
    limit = int(len(layered_candidates) * window_quantifier)
    windows_added = 0
    for i, side in enumerate(layered_candidates):
        d = directions[i]
        for b in side:
            if rng.random() < window_quantifier:
                win = Placeable("WINDOW", b.x + d[0], b.y, b.z + d[1])
                b.tags.append(win)
                windows_added += 1
                if windows_added >= limit:
                    return
    return


def _create_maximalist_windows(
    layered_candidates: list[list[Placeable]], window_quantifier: float, rng: random.Random
):
    return _create_symmetric_windows(layered_candidates, window_quantifier * 2, rng)


def _create_default_windows(
    layered_candidates: list[list[Placeable]], window_quantifier: float, rng: random.Random
):
    return _create_symmetric_windows(layered_candidates, window_quantifier / 2, rng)


def _create_symmetric_windows(
    layered_candidates: list[list[Placeable]],
    window_quantifier: float,
    rng: random.Random,
):
    limit = int(sum([len(i) for i in layered_candidates]) * window_quantifier)
    windows_added = 0
    for i, side in enumerate(layered_candidates):
        d = directions[i]
        for b in side:
            # check the side opposite to the window
            axis = 0 if d[0] != 0 else 1
            if axis == 0:
                cond = lambda x: x.z == b.z
            else:
                cond = lambda x: x.x == b.x
            opposite_candidates = [
                c for c in layered_candidates[(i + 2) % 4] if cond(c)
            ]

            if len(opposite_candidates) == 0:
                continue

            o = rng.choice(opposite_candidates)

            if rng.random() < window_quantifier:
                win = Placeable("WINDOW", b.x + d[0], b.y, b.z + d[1])
                b.tags.append(win)

                # also add opposite window
                win = Placeable("WINDOW", o.x - d[0], o.y, o.z - d[1])
                o.tags.append(win)
                layered_candidates[(i + 2) % 4].remove(o)
                side.remove(b)
                windows_added += 2

                if windows_added >= limit:
                    return
    return
