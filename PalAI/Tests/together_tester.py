import os
import yaml
from configparser import RawConfigParser
from PalAI.Server.LLMClients import together_client

os.chdir(os.path.dirname(__file__))

with open(os.path.join(os.path.dirname(__file__), '..\..\prompts.yaml'), 'r') as file:
    prompts_file = yaml.safe_load(file)


    together = together_client.TogetherClient(prompts_file)


    together.GetOutput("I want a tiny house")