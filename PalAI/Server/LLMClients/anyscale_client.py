import openai
from PalAI.Server.LLMClients.llm_client import LLMClient

# Pricing: https://docs.endpoints.anyscale.com/pricing/


class AnyscaleClient(LLMClient):

    def __init__(self, prompts_file):
        LLMClient.__init__(self, prompts_file)
        self.api_key = self.config.get('anyscale', 'api_key')
        self.model_name = 'mistralai/Mistral-7B-Instruct-v0.1'
        self.model_name = 'meta-llama/Llama-2-7b-chat-hf'
        self.model_name = 'meta-llama/Llama-2-13b-chat-hf'
        self.price_rate = 0.00000025
        self.model_name = 'google/gemma-7b-it'
        self.price_rate = 0.00000015

        self.client = openai.OpenAI(
            base_url="https://api.endpoints.anyscale.com/v1",
            api_key=self.api_key
        )

    async def get_llm_response(self, system_message, prompt, image_path="", debug=False):



          prompt_array = prompt.split('\n')
          user = []
          assistant = []
          bUser = False
          bAssistant = False
          for p in prompt_array:
            if("user" in p.lower()):
                bUser = True
                bAssistant = False
            if ("assistant" in p.lower()):
                bAssistant = True
                bUser = False

            if(bUser):
                user.append(p)

            elif (bAssistant):
                assistant.append(p)


          messages = []
          messages.append({"role": "system", "content": system_message})

          for i, user_prompt in enumerate(user):
              messages.append({"role": "user", "content": user_prompt})
              messages.append({"role": "assistant", "content": assistant[i]})

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


