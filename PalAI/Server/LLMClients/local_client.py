from configparser import RawConfigParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from langchain_community.chat_models.huggingface import ChatHuggingFace
from langchain.schema.messages import HumanMessage
from PalAI.Server.LLMClients.llm_client import LLMClient
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline, GenerationConfig
from langchain_core.output_parsers import StrOutputParser
import torch
from colorama import Fore
import os
import yaml
from PalAI.Server.LLMClients.Examples import mistral_examples


class LocalClient(LLMClient):

    def __init__(self, prompts_file, **kwargs):
        LLMClient.__init__(self, prompts_file)

        # self.model_name = self.config.get('openai', 'model_name')
        self.verbose = kwargs.get("verbose", False)
        self.device = kwargs.get("device", "cuda")
        # Get Model Name
        self.model_name = kwargs.get("model_name", "mistralai/Mistral-7B-Instruct-v0.1")
        # Load Model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name, device_map="cuda", torch_dtype=torch.bfloat16
        )
        # Load Configuration
        # generation_config = GenerationConfig(torch_dtype = torch.bfloat16, temperature = 0.1, do_sample=True, top_k=50)
        # generation_config.save_pretrained('mistalai/Mistral-7B-Instruct-v0.1', push_to_hub=True)
        self.tokenizer = AutoTokenizer.from_pretrained(
            "mistralai/Mistral-7B-Instruct-v0.1"
        )

        # https://huggingface.co/docs/transformers/main/en/main_classes/pipelines

        self.pipe = pipeline(
            "text-generation", model=self.model, tokenizer=self.tokenizer
        )
        self.hf = HuggingFacePipeline(pipeline=self.pipe)
        self.price_rate = 0

    async def get_agent_response(self, agent, prompt):
        system_message = ""
        match agent:
            case "architect":
                system_message = self.prompts_file["architect"]
            case "bricklayer":
                system_message = self.prompts_file["bricklayer"]
            case "materials":
                system_message = self.prompts_file["materials"]
                materials = kwargs.get("materials", "")
                styles = kwargs.get("styles", "")
                system_message.format(materials=materials, styles = styles)
            case "add_ons":
                system_message = self.prompts_file["add_ons"]
            case _:
                system_message = self.prompts_file["architect"]


        messages = self.preparePrompt(prompt, agent)
        kwargs["messages"] = messages
        return await self.get_llm_response(system_message, prompt, **kwargs)

    async def get_llm_response(self, system_message, prompt, **kwargs):

        if self.verbose:
            print(f"{Fore.GREEN}System message:{Fore.RESET} {system_message}")
            print(f"{Fore.BLUE}Prompt:{Fore.RESET} {prompt}")

        self.prompt_total += system_message
        self.prompt_total += prompt
        messages = kwargs.get("messages", [])

        length = 0
        for m in messages:
            length += len(m["content"])
        encodeds = self.tokenizer.apply_chat_template(messages, return_tensors="pt")

        model_inputs = encodeds.to("cuda")
        self.model.to("cuda")
        generated_ids = self.model.generate(
            model_inputs,
            max_new_tokens=300,
            do_sample=True,
            temperature=0.1,
            num_return_sequences=1,
            pad_token_id=self.tokenizer.eos_token_id,
        )  # , repetition_penalty=0.0)

        decoded = self.tokenizer.batch_decode(generated_ids)
        response = decoded[0]
        # print("--------------------------------------------------------- \n LLM RESPONSE " + str(response))
        # if self.verbose:
        #    print(f"{colorama.Fore.CYAN}Response:{colorama.Fore.RESET} {response}")

        response = self.extractResponse(response, messages, type, length)
        if self.verbose:
            print(f"{Fore.CYAN} Filtered LLM RESPONSE: {Fore.RESET}\n" + str(response))

        return response

    def extractResponse(self, response, messages, type="normal", length=0):

        response = (
            response.replace("[/INST]", "")
            .replace("[INST]", "")
            .replace("</s>", "")
            .replace("<s>", "")
            .replace("  ", "")
        )

        #        if (type == "materials"):
        response = response[length + 1 :]
        #            print("Total:" + response + "\n Length:" + str(length))
        #        else:
        #            for m in messages:
        #                response = response.replace(m["content"], "")
        response = response.replace("\n \n", "")

        return response

    def preparePrompt(self, prompt, type):

        prompt = prompt.replace("USER: ", "")
        prompt = prompt.replace("ARCHITECT:", "")
        prompt = prompt.replace("ASSISTANT:", "")
        prompt = prompt.replace("\n", "")

        if type == "architect":
            # print("Architect: \n" + prompt)
            messages = mistral_examples.getArchitectExamples(prompt)
        elif type == "bricklayer":
            # print("Bricklayer: \n" + prompt)
            messages = mistral_examples.getBrickExamples(prompt)
        elif type == "materials":
            # print("Materials: \n" + prompt)
            messages = mistral_examples.getMaterialExamples(prompt)
        elif type == "addons":
            # print("Addons: \n" + prompt)
            messages = mistral_examples.getAddOnsExamples(prompt)
        else:
            messages = mistral_examples.getArchitectExamples(prompt)

        return messages


if __name__ == "main":
    with open(
        os.path.join(os.path.dirname(__file__), "../../../../prompts.yaml"), "r"
    ) as file:
        prompts_file = yaml.safe_load(file)
    example = prompts_file["basic_example"]
    system = prompts_file.get("system_prompt", "").format(example=example)

    prompt = "I want a tiny house"

    client = LocalClient(prompts_file, verbose=True)
    print(client.get_llm_response(system, prompt))
# from configparser import RawConfigParser
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
