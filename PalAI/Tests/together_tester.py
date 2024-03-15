import os
import yaml
from configparser import RawConfigParser
from PalAI.Server.LLMClients import together_client
from PalAI.Server.pal_ai import PalAI
import asyncio

os.chdir(os.path.dirname(__file__))



def test1():

    with open(os.path.join(os.path.dirname(__file__), '..\..\prompts.yaml'), 'r') as file:
        prompts_file = yaml.safe_load(file)

        pal_ai = PalAI(prompts_file, "together")

        architect_plan = await pal_ai.llm_client.get_llm_response(prompts_file["plan_system_message"],
                                         "I want a small house")
        api_result = {"architect": [l for l in architect_plan.split("\n") if l != ""]}

        print(api_result)


test1()