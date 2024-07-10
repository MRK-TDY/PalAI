import json
from enum import StrEnum
from typing import Self


class Placeable:
    class BlockType(StrEnum):
        CUBE = "CUBE"
        CYLINDER = "CYLINDER"
        DIAGONAL = "DIAGONAL"
        ROUNDED_CORNER = "ROUNDED CORNER"
        CONCAVE_CURVE = "CONCAVE CURVE"
        CONVEX_CURVE = "CONVEX CURVE"
        WINDOW = "WINDOW"
        DOOR = "DOOR"
        SMALL_GARDEN = "SMALL GARDEN"
        LARGE_GARDEN = "LARGE GARDEN"
        GARDEN_LIGHT = "GARDEN LIGHT"

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
        self._add_ons = []
        self._additional_keys = {}

    def to_json(self):
        aux = {"type": self.block_type.value, "position": self.position}

        if self.rotation != 0:
            aux["rotation"] = self.rotation
        if self._add_ons is not None and len(self._add_ons) > 0:
            aux["tags"] = [i.to_json() for i in self._add_ons]
        return aux

    @classmethod
    def from_json(cls, data: dict) -> Self:
        block_type = Placeable.BlockType.from_str(data["type"])
        x, y, z = map(
            float,
            data["position"].replace("(", "").replace(")", "").split(","),
        )
        aux = cls(block_type, x, y, z)
        if "rotation" in data:
            aux.rotation = int(data["rotation"])
        if "tags" in data:
            aux.tags = [cls.from_json(i) for i in data["tags"]]
        return aux

    @property
    def tags(self) -> Self:
        return self._add_ons

    @tags.setter
    def tags(self, value: Self):
        self._add_ons = value

    # Backwards compatibility
    @property
    def position(self) -> str:
        return f"({self.x},{self.y},{self.z})"

    def has_door(self) -> bool:
        if self.tags is None:
            return False
        return any(t.block_type == Placeable.BlockType.DOOR for t in self.tags)

    def has_window(self) -> bool:
        if self.tags is None:
            return False
        return any(t.block_type == Placeable.BlockType.WINDOW for t in self.tags)

    @position.setter
    def position(self, value: str):
        value = value.replace("(", "").replace(")", "").split(",")
        self.x = value[0]
        self.y = value[1]
        self.z = value[2]

    def __repr__(self):
        return json.dumps(self.to_json(), indent=2)

    def __setitem__(self, key: str, value):
        if key == "type":
            self.block_type = Placeable.BlockType.from_str(value)
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
