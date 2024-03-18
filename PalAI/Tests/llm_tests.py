import os
import yaml
from configparser import RawConfigParser
from PalAI.Server.LLMClients import together_client
from PalAI.Server.pal_ai import PalAI
import asyncio
import time
os.chdir(os.path.dirname(__file__))




def test_runner(endpoint, prompt):
    with open(os.path.join(os.path.dirname(__file__), '..\..\prompts.yaml'), 'r') as file:
        prompts_file = yaml.safe_load(file)

        pal_ai = PalAI(prompts_file, endpoint)

        architect_plan = asyncio.run(get_architect_plan(prompt, pal_ai, prompts_file))

        layers = asyncio.run(layerbuilder(architect_plan, pal_ai))




async def get_architect_plan(prompt, pal_ai, prompts_file):

    architect_plan = await pal_ai.llm_client.get_llm_response(prompts_file["plan_system_message"],
                                                              prompt + "\nARCHITECT:")
    #api_result = {"architect": [l for l in architect_plan.split("\n") if l != ""]}

    print("Architect Plan: \n " + str(architect_plan))

    return architect_plan


async def layerbuilder(architect_plan, pal_ai):

    building = []
    temp_files_to_delete = []
    history = []
    system_message_template, prompt_template = pal_ai.format_prompt()
    plan_array = architect_plan.split("\n")

    plan_list = [i for i in plan_array if "layer" in i.lower()]

    for i, layer_prompt in enumerate(plan_list):
        current_layer_prompt = pal_ai.prompt_template.format(prompt=layer_prompt, layer=i)
        print("Layer " + str(i) + " \n Prompt: \n" + str(current_layer_prompt))
        if len(history) > 0:
            complete_history = ('\n\n').join(history)
            formatted_prompt = f"Current request: {current_layer_prompt}\n\nHere are the previous layers:\n{complete_history}"
        else:
            formatted_prompt = current_layer_prompt

        if i == 0:
            example = pal_ai.prompts_file["basic_example"]
        else:
            example = pal_ai.prompts_file["basic_example"]

        system_message = system_message_template.format(example=example)

        response = await  pal_ai.llm_client.get_llm_response(system_message, formatted_prompt)
        history.append(f"Layer {i}:")
        history.append(current_layer_prompt)
        history.append(pal_ai.extract_history(formatted_prompt, response))
        new_layer = pal_ai.extract_building_information(response, i)
        building.extend(new_layer)

    print("Final Building \n" + str(building))


if __name__ == '__main__':
    # Record the start time
    start_time = time.time()
    test_runner('anyscale', 'i want a tiny house')

    # Record the end time
    end_time = time.time()

    # Calculate and print the total runtime
    runtime = end_time - start_time
    print(f"The program took {runtime} seconds to run.")