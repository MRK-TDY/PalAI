import os

class ObjVisualizer:
    def __init__(self):
        # Dictionary mapping block names to OBJ file paths
        self.block_obj_paths = {
            'CUBE': 'Blocks/Cube_Block.obj',
            'CHIPPED_CUBE': 'Blocks/Cube_Block.obj',
            'CONCAVE_CUBE': 'Blocks/Cube_Block.obj'
            # Add more block types here
        }

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
                add_ons = block.get("tags", [])
                # size = float(block['size'])
                size = 1
                if "Door" in add_ons:
                    size = 0.8
            except Exception as _:
                continue

            path = os.path.join(os.path.dirname(__file__), self.block_obj_paths[block_name])
            # Load the template OBJ for this block
            with open(path) as file:
                block_obj = file.read()

            # Adjust the vertices based on position and size
            for line in block_obj.splitlines():
                if line.startswith('v '):  # Vertex definition
                    parts = line.split()
                    x, y, z = [float(parts[1]) * size + position[0],
                               float(parts[2]) * size + position[1],
                               float(parts[3]) * size + position[2]]
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

        return obj_content
