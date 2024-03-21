import openai
from PalAI.Server.LLMClients.llm_client import LLMClient

# Pricing: https://docs.endpoints.anyscale.com/pricing/


class AnyscaleClient(LLMClient):

    def __init__(self, prompts_file):
        LLMClient.__init__(self, prompts_file)
        self.api_key = self.config.get('anyscale', 'api_key')
        self.model_name = 'mistralai/Mistral-7B-Instruct-v0.1'

        self.client = openai.OpenAI(
            base_url="https://api.endpoints.anyscale.com/v1",
            api_key=self.api_key
        )



    async def get_llm_response(self, system_message, prompt, image_path="", debug=False):

          user, assistant, instructions = self.preparePrompt(system_message)

          messages = []

          messages.append({"role": "system", "content": instructions})

          for i, user_prompt in enumerate(user):
              messages.append({"role": "user", "content": user_prompt})
              messages.append({"role": "assistant", "content": assistant[i]})

          prompt = prompt.replace("ARCHITECT:\n", "")
          messages.append({"role": "user", "content": prompt})

          self.prompt_total += system_message
          self.prompt_total += prompt

          # Note: not all arguments are currently supported and will be ignored by the backend.
          chat_completion = self.client.chat.completions.create(
              model=self.model_name,
              messages=messages,
              temperature=0.1
          )

          if(debug):
              print(chat_completion.choices[0].message.content)


          return chat_completion.choices[0].message.content


