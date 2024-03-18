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


        self.system_prompt = "You are a virtual architect for a game called TODAY. Your job is to respond to user's requests and plan out in detail the building they want to construct.\n" \
                             "Buildings are created layer by layer, and can be 3 layers tall, labelled from 0 to 2. Buildings are made up of cubes." \
                             "  The first layer, layer 0 is directly above the ground. The higher the number of the layer the higher it is placed." \
                             "  Buildings in today should be solid, which means that if the player requests a square house, instead of making it just the walls, you should fill the insides with cubes as well." \
                             "  In other words, if a player wants a square house you should build a complete 5 by 5 square that is 3 layers tall." \
                             "  In addition, buildings should have some structural integrity, so blocks can't be floating or unsupported." \
                             "  Structures should also maintain some realism, meaning that you shouldn't build structures that are impossible to support." \
                             "  Use natural language when describing the plans for the buildings. Use expressions like create a row of blocks at..., etc..."

        self.system_prompt2 = "ARCHITECT: In order to build a house that widens at the top we must place 3 square shapes on top of each other.\n" \
                              "  Layer 0: A square shape 4 blocks wide.\n" \
                              "  Layer 1: Here we repeat the last layer, placing again a square shape 4 blocks wide.\n" \
                              "  Layer 2: We widen the shape according to the user request."


        self.system_prompt3 = "In order to build an L shaped house we must place 4 square shapes on the ground, there's no need for other layers. \n" \
                              "  Layer 0: 4 blocks in a row from to form the long side of the L shape, with 2 blocks at the end in an angle to form the short side."

    async def get_llm_response(self, system_message, prompt, image_path=""):

          actual_prompt = self.prompts_file["plan_system_message"]
          actual_prompt += prompt

          # Note: not all arguments are currently supported and will be ignored by the backend.
          chat_completion = self.client.chat.completions.create(
              model="mistralai/Mistral-7B-Instruct-v0.1",
              messages=[{"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}],
              temperature=0.1
          )
          print(chat_completion.choices[0].message.content)


          return chat_completion.choices[0].message.content


