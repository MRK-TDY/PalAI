import os
import yaml
from configparser import RawConfigParser
from PalAI.Server.LLMClients import together_client
from PalAI.Server.pal_ai import PalAI
import asyncio

os.chdir(os.path.dirname(__file__))

with open(os.path.join(os.path.dirname(__file__), '..\..\prompts.yaml'), 'r') as file:
    prompts_file = yaml.safe_load(file)


    pal_ai = PalAI(prompts_file, "together")
    result = asyncio.run(pal_ai.build("I want a tiny house"))

    print(result)