
class Prefab:
    def __init__(self, name: str, rotation: int, asset_names: list[str], adjacency_rules: list[str], limit: int = 0):
        self.name = name
        self.asset_names = asset_names
        self.rotation = rotation
        self.adjacency_rules = adjacency_rules
        self.limit = limit

