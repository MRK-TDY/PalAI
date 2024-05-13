import openai
from PalAI.Server.LLMClients.llm_client import LLMClient

# Pricing: https://docs.endpoints.anyscale.com/pricing/


class AnyscaleClient(LLMClient):

    def __init__(self, prompts_file, logger, **kwargs):
        LLMClient.__init__(self, prompts_file, logger)
        self.logger = logger
        self.api_key = self.config.get("anyscale", "api_key")
        self.model_name = "meta-llama/Meta-Llama-3-70B-Instruct"

        self.verbose = kwargs.get("verbose", False)
        self.client = openai.OpenAI(
            base_url="https://api.endpoints.anyscale.com/v1", api_key=self.api_key
        )

    async def get_llm_response(self, system_message, prompt, image_path="", **kwargs):

        user, assistant, instructions = self.preparePrompt(system_message)

        messages = []

        messages.append({"role": "system", "content": instructions})

        for i, user_prompt in enumerate(user):
            messages.append({"role": "user", "content": user_prompt + "\n"})
            messages.append({"role": "assistant", "content": assistant[i] + "\n"})

        prompt = prompt.replace("ARCHITECT:\n", "")
        messages.append({"role": "user", "content": prompt})

        self.prompt_total += system_message
        self.prompt_total += prompt

        # Note: not all arguments are currently supported and will be ignored by the backend.
        chat_completion = self.client.chat.completions.create(
            model=self.model_name, messages=messages, temperature=0.1
        )

        if self.verbose:
            self.logger.info(chat_completion.choices[0].message.content)

        return chat_completion.choices[0].message.content

    def _get_agent_system_message(self, agent, **kwargs):
        system_message = ""
        match agent:
            case "architect":
                system_message = self.prompts_file["architect"]
                system_message = system_message.format(
                    presets=kwargs.get("presets", "")
                )
            case "bricklayer":
                system_message = self.prompts_file["bricklayer"]
            case "materials":
                system_message = self.prompts_file["materials"]
                materials = kwargs.get("materials", "")
                styles = kwargs.get("styles", "")
                system_message = system_message.format(
                    materials=materials, styles=styles
                )
            case "add_ons":
                system_message = self.prompts_file["add_ons"]
            case _:
                system_message = self.prompts_file["architect"]
        return system_message

    async def get_agent_response(self, agent, prompt, **kwargs):
        system_message = self._get_agent_system_message(agent, **kwargs)

        return await self.get_llm_response(system_message, prompt, **kwargs)


    def extractResponse(self, user, assistant, request, response):

        for u in user:
            response.replace(u, "")

        for a in assistant:
            response.replace(a, "")

        for r in request:
            response.replace(r, "")

        return response
