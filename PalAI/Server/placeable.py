import json
from typing import Self
from enum import StrEnum


class Placeable:
    class BlockType(StrEnum):
        CUBE = "CUBE"
        CYLINDER = "CYLINDER"
        DIAGONAL = "DIAGONAL"
        ROUNDED_CORNER = "ROUNDED CORNER"
        WINDOW = "WINDOW"
        DOOR = "DOOR"

        @classmethod
        def from_str(cls, value: str):
            for block_type in cls:
                if block_type.value == value:
                    return block_type
            raise ValueError(f"Invalid block type: {value}")

    def __init__(self, block_type: BlockType, x: int, y: int, z: int) -> Self:
        if type(block_type) is str:
            block_type = Placeable.BlockType.from_str(block_type)
        self.block_type = block_type
        self.x = x
        self.y = y
        self.z = z
        self.rotation = 0
        self._add_ons = None
        self._additional_keys = {}

    def to_json(self):
        aux = {"type": self.block_type.value, "position": self.position}
        if self.rotation != 0:
            aux["rotation"] = self.rotation
        return aux

    @property
    def tag(self) -> Self:
        return self._add_ons

    @tag.setter
    def tag(self, value: Self):
        self._add_ons = value

    # Backwards compatibility
    @property
    def position(self) -> str:
        return f"({self.x},{self.y},{self.z})"

    @position.setter
    def position(self, value: str):
        value = value.replace("(", "").replace(")", "").split(",")
        self.x = value[0]
        self.y = value[1]
        self.z = value[2]

    def __repr__(self):
        return json.dumps(self.to_json(), indent = 2)

    def __setitem__(self, key: str, value):
        if key == "type":
            self.block_type = value
        elif key == "position":
            self.position = value
        elif key == "tags":
            self._add_ons = value
        elif key == "rotation":
            self.rotation = int(value) % 4
        else:
            self._additional_keys[key] = value

    def __contains__(self, key: str) -> bool:
        return key in ["type", "position", "tags"] or key in self._additional_keys

    def __getitem__(self, key: str):
        if key == "type":
            return self.block_type
        elif key == "position":
            return self.position
        elif key == "tags":
            return self._add_ons
        elif key == "rotation":
            return self.rotation
        else:
            return self._additional_keys[key]
