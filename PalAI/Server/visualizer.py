import os

from numpy import add
from PalAI.Server.placeable import Placeable


class ObjVisualizer:
    def __init__(self):
        """Responsible for generating OBJ files from buildings, can take screenshots to send to multi-modal llm's."""
        # Dictionary mapping block names to OBJ file paths
        self.block_obj_paths = {
            "CUBE": "Blocks/Cube_Block.obj",
            "ROUNDED CORNER": "Blocks/ConvexCurve.obj",
            "DIAGONAL": "Blocks/Diagonal.obj",
            "CYLINDER": "Blocks/Cylinder.obj",
            "SMALL GARDEN": "Blocks/Cube_Block.obj",
            "LARGE GARDEN": "Blocks/long_cube.obj",
            "CONVEX CURVE": "Blocks/ConvexCurve.obj",
            "CONCAVE CURVE": "Blocks/Concave.obj",
            # Add more block types here
        }

    def __place_block(self, position, block_name, size, vertex_offset, rotation=0):
        """Places a block in the OBJ file

        :param position: (x, y, z) position of the block
        :type position: tuple
        :param block_name: name of the block, matching the keys in self.block_obj_paths
        :type block_name: str
        :param size: size of the block
        :type size: float
        :param vertex_offset: vertex offset of the OBJ file
        :type vertex_offset: int
        :param rotation: rotation, in increments of 90 degrees along the y-axis
        :type rotation: int in the interval [0- 3]
        :return: content of the OBJ file and the updated vertex offset
        :rtype: tuple (content: str, vertex_offset: int)
        """
        obj_content = ""
        path = os.path.join(os.path.dirname(__file__), self.block_obj_paths[block_name])
        # Load the template OBJ for this block
        with open(path) as file:
            block_obj = file.read()

        # Adjust the vertices based on position and size
        for line in block_obj.splitlines():
            if line.startswith("v "):  # Vertex definition
                parts = line.split()
                x, y, z = [float(parts[1]), float(parts[2]), float(parts[3])]

                # Adjust for pivot (0.5, 0.5) before rotation
                x -= 0.5
                z -= 0.5

                # Apply rotation
                if rotation % 4 == 1:
                    x, z = -z, x
                elif rotation % 4 == 2:
                    x, z = -x, -z
                elif rotation % 4 == 3:
                    x, z = z, -x

                # Adjust back after rotation
                x += 0.5
                z += 0.5

                # Now apply scaling and translation
                x, y, z = [
                    x * size + position[0],
                    y * size + position[1],
                    z * size + position[2],
                ]

                obj_content += f"v {x} {y} {z}\n"
            elif line.startswith(
                "f "
            ):  # Face definition, adjust with the current vertex offset
                parts = line.split()[1:]
                faces = []
                for f in parts:
                    face = f.split("/")
                    face[0] = str(int(face[0]) + vertex_offset)
                    faces.append("/".join(face))
                obj_content += "f " + " ".join(faces) + "\n"
            elif line.startswith("vt "):
                obj_content += line + "\n"
            elif line.startswith("vn "):
                obj_content += line + "\n"

        # Update the vertex offset for the next block
        vertex_offset += sum(
            1 for line in block_obj.splitlines() if line.startswith("v ")
        )
        return (obj_content, vertex_offset)

    def generate_obj(self, api_response):
        """Takes an API response and generates an OBJ file representation.

        :param api_response: building data in the format of the API response
        :type api_response: list(dict)
        :return: content of the OBJ file
        :rtype: str
        """

        obj_content = ""
        vertex_offset = 0  # Initialize vertex offset

        for block in api_response:
            if isinstance(block, Placeable):
                block = block.to_json()
            if block["type"] not in self.block_obj_paths:
                print("Block type not implemented:", block["type"])
                block["type"] = (
                    "CUBE"  # Default to a cube if the block type is not implemented
                )

            block_name = block["type"]
            position = tuple(
                map(
                    float,
                    block["position"].replace("(", "").replace(")", "").split(","),
                )
            )
            size = 1
            if "GARDEN" in block_name:
                position = (position[0] + 0.25, position[1], position[2] + 0.25)
                size = 0.5

            rotation = block.get("rotation", 0 )
            for add_on in block.get("tags", [] ):
                # add_on_size = float(block['add_on_size'])
                add_on_size = 0.3 if add_on["type"] == "WINDOW" else 0.5
                pos = add_on["position"].replace("(", "").replace(")", "").split(",")
                diff = (position[0] - float(pos[0]), position[2] - float(pos[2]))
                add_on_position = (
                    0.35 + float(pos[0]) + diff[0] * 0.5,
                    0.5 + float(pos[1]),
                    0.35 + float(pos[2]) + diff[1] * 0.5,
                )
                placed_block = self.__place_block(
                    add_on_position, "CUBE", add_on_size, vertex_offset
                )
                obj_content += placed_block[0]
                vertex_offset = placed_block[1]
                if add_on["type"] == "DOOR":
                    add_on_position = (
                            add_on_position[0],
                            add_on_position[1] - 0.4,
                            add_on_position[2]
                    )
                    placed_block = self.__place_block(
                        add_on_position, "CUBE", add_on_size, vertex_offset
                    )
                    obj_content += placed_block[0]
                    vertex_offset = placed_block[1]

            placed_block = self.__place_block(
                position, block_name, size, vertex_offset, rotation
            )
            obj_content += placed_block[0]
            vertex_offset = placed_block[1]

        return obj_content
