import os
from configparser import RawConfigParser


class LLMClient:

    def __init__(self, prompts_file):
        """Abstract class representing a client for any LLM

        :param prompts_file: prompts to be used
        :type prompts_file: dict
        """
        self.prompts_file = prompts_file
        self.system_prompt = self.prompts_file.get("system_prompt", "")
        self.prompt_template = self.prompts_file.get("prompt_template", "")
        self.prompt_total = ""
        self.price_rate = 0.00000015
        os.chdir(os.path.dirname(__file__))

        self.config = RawConfigParser()
        self.config.read("../../../config.ini")
        self.temperature = float(self.config.get("llm", "temperature"))
        self.max_tokens = int(self.config.get("llm", "max_tokens"))
        self.verbose = bool(self.config.get("llm", "verbose"))

    async def get_llm_response(self, system_message, prompt, image_path=""):
        pass


    async def get_agent_response(self, agent, prompt, **kwargs):
        system_message = ""
        match agent:
            case "architect":
                system_message = self.prompts_file["architect"]
            case "bricklayer":
                system_message = self.prompts_file["bricklayer"]
            case "materials":
                system_message = self.prompts_file["house_design"]
                materials = kwargs.get("materials", "")
                styles = kwargs.get("styles", "")
                system_message.format(materials=materials, styles = styles)
            case "add_ons":
                system_message = self.prompts_file["addons"]
            case _:
                system_message = self.prompts_file["architect"]


        return self.get_llm_response(system_message, prompt, **kwargs)

    def getTotalPromptsUsed(self):
        return self.prompt_total

    # When it is necessary to treat the prompt more carefully. When systems need user -> assistant type of queries
    def preparePrompt(self, system_message):
        prompt_array = system_message.split("\n")
        user = []
        assistant = [""]
        instructions = ""
        assistant_index = 0
        bUser = False
        bAssistant = False
        for p in prompt_array:
            if len(p) < 2:
                continue
            if "EXAMPLE" in p:
                continue
            if "USER" in p:
                bUser = True
                bAssistant = False
            if "ARCHITECT" in p:
                bAssistant = True
                bUser = False
                assistant_index += 1

            if bUser:
                user.append(p)

            elif bAssistant:
                if len(assistant) <= assistant_index:
                    assistant.append(p)
                else:
                    assistant[assistant_index] += p

            else:
                instructions += p

        return user, assistant, instructions

    def SetModel(self, model_name):
        self.model_name = model_name

        if "13b" in model_name:
            self.price_rate = 0.00000025
        else:
            self.price_rate = 0.00000015

    async def get_llm_single_response(
        self, context_type, context_file, prompt, debug=False
    ):

        system_message = context_file[context_type + "_system_message"]
        examples = context_file[context_type + "_examples"]
        user = []
        assistant = []
        for key in examples.keys():
            user.append(examples[key]["user"])
            assistant.append(examples[key]["assistant"])

        messages = []
        messages.append({"role": "system", "content": system_message})
        self.prompt_total += system_message

        for i, user_prompt in enumerate(user):
            messages.append({"role": "user", "content": user_prompt})
            messages.append({"role": "assistant", "content": assistant[i]})
            self.prompt_total += user_prompt
            self.prompt_total += assistant[i]

        prompt = prompt.replace("ARCHITECT:\n", "")
        messages.append({"role": "user", "content": prompt})

        self.prompt_total += prompt

        # Note: not all arguments are currently supported and will be ignored by the backend.
        chat_completion = self.client.chat.completions.create(
            model=self.model_name, messages=messages, temperature=0.1
        )

        if debug:
            print(chat_completion.choices[0].message.content)

        self.prompt_total += chat_completion.choices[0].message.content

        return chat_completion.choices[0].message.content
