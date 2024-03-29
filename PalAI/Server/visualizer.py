import os

class ObjVisualizer:
    def __init__(self):
        # Dictionary mapping block names to OBJ file paths
        self.block_obj_paths = {
            'CUBE': 'Blocks/Cube_Block.obj',
            'ROUNDED CORNER': 'Blocks/ConvexCurve.obj',
            'DIAGONAL': 'Blocks/Diagonal.obj',
            'CYLINDER': 'Blocks/Cylinder.obj'
            # Add more block types here
        }

    def __place_block(self, position, block_name, size, vertex_offset, rotation = 0):
        obj_content = ''
        path = os.path.join(os.path.dirname(__file__), self.block_obj_paths[block_name])
        # Load the template OBJ for this block
        with open(path) as file:
            block_obj = file.read()

        # Adjust the vertices based on position and size
        for line in block_obj.splitlines():
            if line.startswith('v '):  # Vertex definition
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
                x, y, z = [x * size + position[0], y * size + position[1], z * size + position[2]]

                obj_content += f'v {x} {y} {z}\n'
            elif line.startswith('f '):  # Face definition, adjust with the current vertex offset
                parts = line.split()[1:]
                faces = []
                for f in parts:
                    face = f.split('/')
                    face[0] = str(int(face[0]) + vertex_offset)
                    faces.append('/'.join(face))
                obj_content += 'f ' + ' '.join(faces) + '\n'
            elif line.startswith('vt '):
                obj_content += line + '\n'
            elif line.startswith('vn '):
                obj_content += line + '\n'

        # Update the vertex offset for the next block
        vertex_offset += sum(1 for line in block_obj.splitlines() if line.startswith('v '))
        return (obj_content, vertex_offset)


    def generate_obj(self, api_response):
        """
        Takes an API response and generates an OBJ file representation.

        Parameters:
        - api_response: A list of dictionaries, where each dictionary represents a block.

        Returns:
        - A string representing the content of an OBJ file.
        """
        obj_content = ''
        vertex_offset = 0  # Initialize vertex offset

        for block in api_response:
            if block['type'] not in self.block_obj_paths:
                print("Block type not implemented:", block['type'])
                block['type'] = 'CUBE'  # Default to a cube if the block type is not implemented

            try:
                block_name = block['type']
                position = tuple(map(float, block['position'].replace("(", "").replace(")", "").split(',')))
                rotation = block.get("rotation", 0)
                add_on = block.get("tags", {})
                # size = float(block['size'])
                size = 1
                if add_on.get("type", "") in ["WINDOW", "DOOR"]:
                    add_on_position = tuple(map(lambda x: float(x), add_on['position'].replace("(", "").replace(")", "").split(',')))
                    placed_block = self.__place_block(add_on_position, 'CUBE', 0.3, vertex_offset)
                    obj_content += placed_block[0]
                    vertex_offset = placed_block[1]
            except Exception as _:
                continue
            placed_block = self.__place_block(position, block_name, size, vertex_offset, rotation)
            obj_content += placed_block[0]
            vertex_offset = placed_block[1]


        return obj_content
