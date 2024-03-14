import os
from configparser import RawConfigParser

class LLMClient():

    def __init__(self, prompts_file):
        self.prompts_file = prompts_file
        self.system_prompt = self.prompts_file.get('system_prompt', "")
        self.prompt_template = self.prompts_file.get('prompt_template', "")


        os.chdir(os.path.dirname(__file__))

        self.config = RawConfigParser()
        self.config.read('../../../config.ini')
        self.temperature = float(self.config.get('llm', 'temperature'))
        self.max_tokens = int(self.config.get('llm', 'max_tokens'))
        self.verbose = bool(self.config.get('llm', 'verbose'))


    async def get_llm_response(self, system_message, prompt, image_path=""):
        print(response)