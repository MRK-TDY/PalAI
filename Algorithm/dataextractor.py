from Server import gptlink

default_response = "B:Cube|X=2680.000 Y=-1880.000 Z=110.000|3\n" \
                   "B:Cube|X=2880.000 Y=-2280.000 Z=110.000|3\n" \
                   "B:Cube|X=2880.000 Y=-2081.000 Z=110.000|3\n" \
                   "B:Cube|X=2880.000 Y=-1880.000 Z=110.000|3\n" \
                   "B:Cube|X=3080.000 Y=-1880.000 Z=110.000|3\n"


def extract_data(data):
    print("Extracting data: \n" + str(data))
    result = gptlink.extract(data)
    return result
