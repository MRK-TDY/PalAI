import json


def GetJsonFromData(new_data):
    old_data = """
    B:Cube|X=-100.000 Y=-100.000 Z=125.200|3|P=0.000000 Y=0.000000 R=0.000000
    B:Cube|X=100.000 Y=-100.000 Z=125.200|3|P=0.000000 Y=0.000000 R=0.000000
    B:Cube|X=100.000 Y=100.000 Z=125.200|3|P=0.000000 Y=0.000000 R=0.000000
    B:Cube|X=-100.000 Y=100.000 Z=125.200|3|P=0.000000 Y=0.000000 R=0.000000
    F:Door_Frameless|X=69.594 Y=200.000 Z=98.805|3|X=0.000 Y=1.000 Z=0.000
    M:Honeycomb White
    M:Plastic Orange
    O:Fridge|DT_Kitchen|X=130.000 Y=-160.000 Z=25.542|P=0.000000 Y=0.000000 R=0.000000
    """

    lines = new_data.strip().split('\n')
    materials = []
    decorations = []
    blocks = []

    for line in lines:
        parts = line.split('|')
        category = parts[0].split(':')[0]
        if category == 'M':
            materials.append(parts[0].split(':')[1].strip().upper())
        elif category == 'O':
            type_details = parts[0].split(':')[1].split('|')
            item_type = type_details[0].strip()
            position_details = parts[2].split()
            rotation_details = parts[3].split()
            x, z = float(position_details[0].split('=')[1]), float(position_details[2].split('=')[1])
            rotation = (float(rotation_details[0].split('=')[1]), float(rotation_details[1].split('=')[1]) ,float(rotation_details[1].split('=')[1]))
            rotation = RotationFilter(rotation)
            decorations.append({
                "type": item_type,
                "rotation": str(rotation),  # Placeholder for rotation logic
                "position": f"({int(x)/100},0,{int(z)/100})"
            })
        elif category == 'B':
            position_details = parts[1].split()
            x, z = float(position_details[0].split('=')[1])/100, float(position_details[2].split('=')[1])/100
            blocks.append({
                "type": "CUBE",
                "position": f"({int(x)},0,{int(z)})"
            })

    output = {
        "materials": {
            "FLOOR": materials[0] if len(materials) > 0 else "None",
            "INTERIOR": materials[1] if len(materials) > 1 else "None",
            "EXTERIOR": "None",
            "STYLE": "None"
        },
        "decorations": decorations,
        "result": blocks,
        "event": "result",
        "message": "Data processed"
    }

    return output



def FileManager(filepath):
    f = open(filepath, "r")
    output = GetJsonFromData(f.read())
    f.close()
    # the json file to save the output data
    save_file = open("savedata.json", "w")
    json.dump(output, save_file, indent=4)
    save_file.close()

def RotationFilter(rotation):
    if rotation == (0,0,0):  # 0 degrees, no rotation
        return 0
    elif rotation == (90,0,90) or rotation == (-270,0,0):  # 90 degrees
        return 1
    elif rotation == (180,0,0) or rotation == (-180,0,0):  # 180 degrees
        return 2
    elif rotation == (270,0,0) or rotation == (-90,0,0): # 270 degrees
        return 3

    else:
        return 0


FileManager('output.txt')