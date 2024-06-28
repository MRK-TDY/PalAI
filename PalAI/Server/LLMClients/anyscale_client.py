import openai
from PalAI.Server.LLMClients.llm_client import LLMClient
from loguru import logger

# Pricing: https://docs.endpoints.anyscale.com/pricing/


class AnyscaleClient(LLMClient):

    def __init__(self, prompts_file, **kwargs):
        LLMClient.__init__(self, prompts_file)
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
            logger.info(chat_completion.choices[0].message.content)

        return chat_completion.choices[0].message.content


    def extractResponse(self, user, assistant, request, response):

        for u in user:
            response.replace(u, "")

        for a in assistant:
            response.replace(a, "")

        for r in request:
            response.replace(r, "")

        return response
