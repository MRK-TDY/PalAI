from enum import StrEnum

from PalAI.Server.Decorator.prefab import Prefab

class CellType(StrEnum):
    VALID = "VALID"
    INVALID = "INVALID"
    OUTSIDE = "OUTSIDE"


class Cell:
    def __init__(self, x: int, z: int, cell_type: CellType, possibilities: list[Prefab]):
        self.x = x
        self.z = z
        self.cell_type = cell_type
        self.collapsed = False
        self.possibilities = possibilities
        self.prefab: list[Prefab] = []

    def entropy(self) -> int:
        return 0 if self.collapsed else len(self.possibilities)

    def update(self):
        # TODO: This should change the list of possibilities
        return

    def collapse(self) -> None:
        self.collapsed = True
        self.prefab = self.possibilities[0]

