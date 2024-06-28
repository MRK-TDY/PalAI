import asyncio
import yaml

from PalAI.Tools.LLMClients.parrot_client import ParrotClient
from PalAI.Server.pal_ai import *
from PalAI.Server.visualizer import *
from PalAI.Server.LLMClients import *

def generate_obj(building, name = "test"):
    obj = ObjVisualizer().generate_obj(building)

    with open(os.path.join(os.path.dirname(__file__), f"{name}.obj"), "w") as fptr:
        fptr.write(obj)
        fptr.flush()

def main():
    with open(
        os.path.join(os.path.dirname(__file__), "../../prompts.yaml"), "r"
    ) as file:
        prompts_file = yaml.safe_load(file)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    client = ParrotClient(prompts_file, logger)

    os.makedirs(os.path.join(os.path.dirname(__file__), "output/layers"), exist_ok=True)

    with open(os.path.join(os.path.dirname(__file__), '../Server/layers.json'), 'r') as f:
        aux = json.load(f)
        layers = [i["name"] for i in aux['layers']]

    request = PalAI.PalAIRequest.layers_only()

    for l in layers:
        pal = PalAI(prompts_file, client)

        # run main pipeline
        prompt = l

        api_result = asyncio.run(pal.build(prompt, request_type=request))
        building = api_result["result"]

        generate_obj(building, f"output/layers/{l}")


if __name__ == "__main__":
    main()
