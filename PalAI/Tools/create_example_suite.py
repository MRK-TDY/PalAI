import asyncio
import time
import yaml

from PalAI.Tools.LLMClients.random_client import RandomClient
from PalAI.Server.pal_ai import *
from PalAI.Server.visualizer import *
from PalAI.Server.LLMClients import *

def generate_obj(building, name = "test"):
    obj = ObjVisualizer().generate_obj(building)

    with open(os.path.join(os.path.dirname(__file__), f"{name}.obj"), "w") as fptr:
        fptr.write(obj)
        fptr.flush()



def generate_building(prompts_file, logger, seed):
    rng = random.Random(seed)
    client = RandomClient(prompts_file, logger, rng=rng)
    pal = PalAI(prompts_file, client, None, rng)

    # run main pipeline
    prompt = "Where we're going we don't need prompts"

    api_result = asyncio.run(pal.build(prompt))
    building = api_result["result"]
    building.extend(api_result["garden"])

    with open(os.path.join(os.path.dirname(__file__), f"output/examples/{seed}.json"), "w") as fptr:
        fptr.write(json.dumps(api_result, indent=4))
        fptr.flush()

    generate_obj(building, f"output/examples/{seed}")


def main():
    with open(
        os.path.join(os.path.dirname(__file__), "../../prompts.yaml"), "r"
    ) as file:
        prompts_file = yaml.safe_load(file)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.WARNING)
    file_handler = logging.FileHandler(
        os.path.join(os.path.dirname(__file__), "records.log")
    )
    file_handler.setLevel(logging.WARNING)
    file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter("%(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)


    os.makedirs(os.path.join(os.path.dirname(__file__), "output/examples"), exist_ok=True)
    start_time = time.time()

    for i in range(100):
        generate_building(prompts_file, logger, i)

    print(f"Time taken: {(time.time() - start_time):.2f}")


if __name__ == "__main__":
    main()
