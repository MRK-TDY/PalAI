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
              messages.append({"role": "user", "content": user_prompt + "\n"})
              messages.append({"role": "assistant", "content": assistant[i] + "\n"})

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

          print(chat_completion.choices[0].message.content)
          return chat_completion.choices[0].message.content


    def preparePrompt(self, system_message):
        prompt_array = system_message.split('\n')
        user = []
        assistant = [""]
        instructions = ""
        assistant_index = -1
        bUser = False
        bAssistant = False
        for p in prompt_array:
            if(len(p) < 2):
                continue
            if("EXAMPLE" in p):
                continue
            if ("USER" in p):
                bUser = True
                bAssistant = False
            if ("ARCHITECT" in p):
                bAssistant = True
                bUser = False
                assistant_index += 1

            if (bUser):
                backup = p.replace("USER: ", "")
                user.append(backup + "\n")

            elif (bAssistant):
                if(len(assistant) <= assistant_index):
                    assistant.append(p)
                else:
                    assistant[assistant_index] += p + "\n"

            else:
                instructions += p


        return user, assistant, instructions

