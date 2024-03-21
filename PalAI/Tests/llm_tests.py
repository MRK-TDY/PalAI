import csv
import json
import os
import yaml
from configparser import RawConfigParser
from PalAI.Server.LLMClients import together_client
from PalAI.Server.pal_ai import PalAI
from PalAI.Server.visualizer import ObjVisualizer
import asyncio
import tiktoken
import time
import pandas as pd

os.chdir(os.path.dirname(__file__))

# This limits the number of buildings generated
limit = 1

with open(os.path.join(os.path.dirname(__file__), "Resources/baselines.json"), 'r') as fptr:
    baselines_json = json.load(fptr)

with open(os.path.join(os.path.dirname(__file__), 'Resources/context_prompts.json'), 'r') as bricklayer_file:
    context_json = json.load(bricklayer_file)

def evaluate(prompt, output, key="baselines"):
    if prompt in baselines_json[key].keys():
        current_baseline_blocks = baselines_json[key][prompt]
        max_score = len(current_baseline_blocks)
        print("Expected Layer: " + str(current_baseline_blocks))
        true_positives = 0
        for block in current_baseline_blocks:
            if block in output:
                true_positives += 1

        false_negatives = 0
        for block in current_baseline_blocks:
            if block not in output:
                false_negatives += 1

        false_positives = 0
        for block in output:
            if block not in current_baseline_blocks:
                false_positives += 1

        accuracy = true_positives / (true_positives + false_negatives)
        accuracy = round(accuracy, 3)
        precision = true_positives / (true_positives + false_positives)
        precision = round(precision, 3)
        overall_score = 2 * (precision * accuracy) / (precision + accuracy) if (precision + accuracy) > 0 else 0
        overall_score = round(overall_score, 3)

        ## TODO: Add complexity bonus

        print("Accuracy: " + str(accuracy))
        print("Precision: " + str(precision))
        print("Overall Score: " + str(round(overall_score,4)))


        return accuracy, precision, overall_score

    else:
        print("Output Evaluator: Prompt not in baseline list")
        return 0, 0, 0, 0



def test_runner(endpoint, prompt):
    with open(os.path.join(os.path.dirname(__file__), '..\..\prompts.yaml'), 'r') as file:
        prompts_file = yaml.safe_load(file)

        pal_ai = PalAI(prompts_file, endpoint)

        architect_plan = asyncio.run(pal_ai.build(prompt))

#        layers = asyncio.run(layerbuilder(architect_plan, pal_ai))

        return pal_ai, layers


async def get_architect_plan(prompt, pal_ai, prompts_file, debug=False):

    architect_plan = await pal_ai.llm_client.get_llm_response(prompts_file["plan_system_message"],
                                                              prompt)
    #api_result = {"architect": [l for l in architect_plan.split("\n") if l != ""]}

    if(debug):
        print("Architect Plan: \n " + str(architect_plan))

    return architect_plan


async def layerbuilder(architect_plan, pal_ai):

    building = []
    history = []
    #system_message_template, prompt_template = pal_ai.format_prompt()
    plan_array = architect_plan.split("\n")

    plan_list = [i for i in plan_array if "layer" in i.lower()]

    for i, layer_prompt in enumerate(plan_list):
        current_layer_prompt = pal_ai.prompt_template.format(prompt=layer_prompt, layer=i)

        formatted_prompt = current_layer_prompt
        if i == 0:
            example = pal_ai.prompts_file["basic_example"]
        else:
            example = pal_ai.prompts_file["basic_example"]

        system_message = pal_ai.system_prompt.format(example=example)

        response = await  pal_ai.llm_client.get_llm_response(system_message, formatted_prompt)
        history.append(f"Layer {i}:")
        history.append(current_layer_prompt)
        history.append(pal_ai.extract_history(formatted_prompt, response))
        new_layer = pal_ai.extract_building_information(response, i)
        building.extend(new_layer)

    visual = ObjVisualizer()
    obj_content = visual.generate_obj(building)
    with open(f'temp.obj', 'w') as fptr:
        fptr.write(obj_content)
        fptr.flush()

    return building

def num_tokens_from_string(string: str, encoding_name: str) -> int:
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens



def testsuite():
    with open(os.path.join(os.path.dirname(__file__), 'Resources/prompts.csv'), 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        i = 0
        for row in reader:
            i += 1
            prompt = row["PROMPT"]
            print("--------------------------")
            print("Evaluating Prompt: " + prompt)
            runttest(prompt, 'anyscale')
            if i >= limit:
                return



def runttest(prompt, model_type):
    # Record the start time
    start_time = time.time()
    pal_ai, building = test_runner(model_type, prompt)
    print("Model used: " + pal_ai.llm_client.model_name)
    try:
        if pal_ai:
            total_prompt = pal_ai.llm_client.getTotalPromptsUsed()
            tokens_used = num_tokens_from_string(total_prompt, 'cl100k_base')
            print("Tokens used: " + str(tokens_used))
            price_rate = pal_ai.llm_client.price_rate
            print("Estimated cost: " + str(round(price_rate * tokens_used, 6)) + "$")
    except NameError:
        print("Tokens used: " + str(num_tokens_from_string(prompt, 'cl100k_base')))

    try:
        if building:
            evaluate(prompt, building)
    except NameError:
        print("Prompt not found, result not evaluated")

    # Record the end time
    end_time = time.time()

    # Calculate and print the total runtime
    runtime = end_time - start_time
    print(f"The test took {round(runtime, 4)} seconds to run.")


def save_metrics_to_excel(metrics_list, file_name="Metrics/llm_comparison.xlsx"):
    # Convert the list of dictionaries to a DataFrame
    new_data_df = pd.DataFrame(metrics_list)

    # If the Excel file exists, read it and append the new data
    if os.path.exists(file_name):
        existing_data_df = pd.read_excel(file_name)
        combined_df = pd.concat([existing_data_df, new_data_df], ignore_index=True)
    else:
        combined_df = new_data_df

    # Save the combined DataFrame to Excel, without the index
    combined_df.to_excel(file_name, index=False)


async def testbricklayer(model_type, model_name=None):

    with open(os.path.join(os.path.dirname(__file__), '..\..\prompts.yaml'), 'r') as file:
        prompts_file = yaml.safe_load(file)
        for prompt in baselines_json["bricklayer_baselines"].keys():

            pal_ai = PalAI(prompts_file, model_type)

            if model_name != None:
                pal_ai.llm_client.SetModel(model_name)

            start_time = time.time()
            print("---------------------------------- \nModel used: " + pal_ai.llm_client.model_name)

            response = await pal_ai.llm_client.get_llm_single_response("bricklayer",context_json, prompt)
            #print("LLM Response: " + str(response))
            new_layer = pal_ai.extract_building_information(response, 0)
            print("Prompt: " + prompt + "\nGenerated Layer: " + str(new_layer))
            accuracy, precision, overall_score = evaluate(prompt, new_layer, "bricklayer_baselines")
            total_prompt = pal_ai.llm_client.getTotalPromptsUsed()
            tokens_used = num_tokens_from_string(total_prompt, 'cl100k_base')
            print("Tokens used: " + str(tokens_used))
            price_rate = pal_ai.llm_client.price_rate
            price_total = round(price_rate * tokens_used, 4)
            print("Estimated cost: " + str(round(price_rate * tokens_used, 5)) + "$")

            # Record the end time
            end_time = time.time()

            # Calculate and print the total runtime
            runtime = end_time - start_time
            print(f"The test took {round(runtime, 4)} seconds to run.")

            metrics_list = [{
            'Endpoint': model_type,
            'Model Name': pal_ai.llm_client.model_name,
            'Prompt': prompt,
            'Accuracy Score': accuracy,
            'Precision Score': precision,
            'Overall Score': overall_score,
            'Price Rate': price_rate,
            'Estimated Price Total': price_total,
            'Runtime': round(runtime, 4)}]

            save_metrics_to_excel((metrics_list))




if __name__ == '__main__':
   # asyncio.run(testbricklayer("anyscale"))
   # asyncio.run(testbricklayer("anyscale", 'meta-llama/Llama-2-7b-chat-hf'))
   # asyncio.run(testbricklayer("anyscale", 'meta-llama/Llama-2-13b-chat-hf'))
   # asyncio.run(testbricklayer("anyscale", 'google/gemma-7b-it'))
    asyncio.run(testbricklayer("gpt"))


## Anyscale Model Names
# 'meta-llama/Llama-2-7b-chat-hf'
# 'meta-llama/Llama-2-13b-chat-hf'
# 'google/gemma-7b-it'
# default: 'mistralai/Mistral-7B-Instruct-v0.1'