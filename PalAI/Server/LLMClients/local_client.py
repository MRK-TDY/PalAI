from configparser import RawConfigParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from langchain_community.chat_models.huggingface import ChatHuggingFace
from langchain.schema.messages import HumanMessage
from PalAI.Server.LLMClients.llm_client import LLMClient
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline, GenerationConfig
from langchain_core.output_parsers import StrOutputParser
import torch
import colorama
import os
import yaml
from PalAI.Server.LLMClients.Examples import mistral_examples

class LocalClient(LLMClient):

    def __init__(self, prompts_file, **kwargs):
        LLMClient.__init__(self, prompts_file)

        #self.model_name = self.config.get('openai', 'model_name')
        self.verbose = kwargs.get('verbose', False)
        self.device = kwargs.get('device', 'cuda')
        # Get Model Name
        self.model_name = kwargs.get('model_name', 'mistralai/Mistral-7B-Instruct-v0.1')
        # Load Model
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name, device_map='cuda', torch_dtype=torch.bfloat16)
        #Load Configuration
        #generation_config = GenerationConfig(torch_dtype = torch.bfloat16, temperature = 0.1, do_sample=True, top_k=50)
        #generation_config.save_pretrained('mistalai/Mistral-7B-Instruct-v0.1', push_to_hub=True)
        self.tokenizer = AutoTokenizer.from_pretrained('mistralai/Mistral-7B-Instruct-v0.1')

       # https://huggingface.co/docs/transformers/main/en/main_classes/pipelines
        
        self.pipe = pipeline("text-generation", model=self.model, tokenizer=self.tokenizer)
        self.hf = HuggingFacePipeline(pipeline=self.pipe)
        self.price_rate = 0


    async def get_llm_response(self, system_message, prompt, type='default'):
                
        #if self.verbose:
        #    print(f"{colorama.Fore.GREEN}System message:{colorama.Fore.RESET} {system_message}")
        #    print(f"{colorama.Fore.BLUE}Prompt:{colorama.Fore.RESET} {prompt}")

        self.prompt_total += system_message
        self.prompt_total += prompt

        messages = self.preparePrompt(prompt, type)

        length= len(prompt) + len(system_message)
        encodeds = self.tokenizer.apply_chat_template(messages, return_tensors="pt")

        model_inputs = encodeds.to("cuda")
        self.model.to("cuda")
        generated_ids = self.model.generate(model_inputs, max_new_tokens=250, do_sample=True, temperature=0.1, num_return_sequences=1, pad_token_id=self.tokenizer.eos_token_id) #, repetition_penalty=0.0)
        decoded = self.tokenizer.batch_decode(generated_ids)
        response = decoded[0]

        #if self.verbose:
        #    print(f"{colorama.Fore.CYAN}Response:{colorama.Fore.RESET} {response}")

        #print("---------------------- \n Original LLM RESPONSE: " + str(response))
        response = self.extractResponse(response, messages)
        print("---------------------------------------- \n Filtered LLM RESPONSE: " + str(response))
        print("----------------------------------------------------------")
        return response

    def extractResponse(self, response, messages):
        
        for m in messages:
            response = response.replace(m["content"], "")
        response = response.replace("[/INST]", "")
        response = response.replace("[INST]", "")
        response = response.replace("</s>", "")
        response = response.replace("<s>", "")
        response = response.replace("  ", "")
        response = response.replace("\n \n", "")
        return response

    async def get_llm_single_response(self, context_type,context_file, original_prompt, debug=False):
        print("Single response")
        system_message = context_file[context_type + "_system_message"]
        examples =context_file[context_type + "_examples"]
        user = []
        assistant = []
        for key in examples.keys():
            user.append(examples[key]["user"])
            assistant.append(examples[key]["assistant"])

        messages = []
        messages.append(("system", system_message))
        self.prompt_total += system_message

        for i, user_prompt in enumerate(user):
            messages.append(("user", user_prompt))
            messages.append(("assistant", assistant[i]))
            self.prompt_total += user_prompt
            self.prompt_total += assistant[i]

        self.prompt_total += original_prompt

        prompt = ChatPromptTemplate.from_messages(messages)
        llm = self.llm

        self.chain = prompt | llm | StrOutputParser()
        response = await self.chain.ainvoke({"system_message": system_message, "example": messages, "prompt": original_prompt})

        if self.verbose:
            print(f"{colorama.Fore.CYAN}Response:{colorama.Fore.RESET} {response}")

        return response

    def preparePrompt(self, prompt,type):

        prompt = prompt.replace("USER: ","")
        prompt = prompt.replace("ARCHITECT:", "")
        prompt = prompt.replace("\n", "")

        if (type == 'architect'):
            print("Architect: \n" + prompt)
            messages = mistral_examples.getArchitectExamples(prompt)
        elif (type == 'bricklayer'):
            print("Bricklayer: \n" + prompt)
            messages = mistral_examples.getBrickExamples(prompt)
        elif (type == 'materials'):
            print("Materials: \n" + prompt)
            messages = mistral_examples.getMaterialExamples(prompt)
        elif (type == 'addons'):
            print("Addons: \n" + prompt)
            messages = mistral_examples.getAddOnsExamples(prompt)
        else:
            messages = mistral_examples.getArchitectExamples(prompt)

        return messages




if __name__ == "main":
    with open(os.path.join(os.path.dirname(__file__), '../../../../prompts.yaml'), 'r') as file:
        prompts_file = yaml.safe_load(file)
    example = prompts_file["basic_example"]
    system = prompts_file.get('system_prompt', "").format(example=example)

    prompt = "I want a tiny house"

    client = LocalClient(prompts_file, verbose = True)
    print(client.get_llm_response(system, prompt))
from configparser import RawConfigParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
