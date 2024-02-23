

paths = {
    'CUBE': '../Server/Blocks/Cube_Block.obj',
    'CHIPPED_CUBE': '../Server/Blocks/ChippedCube.obj',
    'CONCAVE_CUBE': '../Server/Blocks/HollowCube.obj',
    'DIAGONAL': '../Server/Blocks/Diagonal_4m_Block.obj'
}

def reader(filename):
    """
    Takes an API response and generates an OBJ file representation.

    Parameters:
    - api_response: A list of dictionaries, where each dictionary represents a block.

    Returns:
    - A string representing the content of an OBJ file.
    """
    obj_content = ''
    vertex_offset = 0  # Initialize vertex offset

    # Using readlines()
    file1 = open(filename, 'r')
    Lines = file1.readlines()

    for L in Lines:

        split = L.split('|')

        type = split[0]
        position = tuple(map(float, split[1].replace("(", "").replace(")", "").split(',')))
        size = 2
        if type in paths.keys():

            with open(paths[type]) as file:
                block_obj = file.read()
            print("Found: " + str(type) + str(position) + str(size))
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

    with open(f'temp.obj', 'w') as fptr:
        fptr.write(obj_content)
        fptr.flush()


reader("Files/response.txt")