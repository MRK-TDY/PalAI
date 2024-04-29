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
from PalAI.Server.LLMClients.Examples import example_getter
from huggingface_hub import login

class LocalClient(LLMClient):

    def __init__(self, prompts_file, logger, **kwargs):
        LLMClient.__init__(self, prompts_file, logger)

        # self.model_name = self.config.get('openai', 'model_name')
        self.logger = logger
        self.verbose = kwargs.get("verbose", False)
        self.device = kwargs.get("device", "cuda")
        login(self.config.get("hugging_face", "login_key"))

        # Get Model Name
        self.model_name = self.config.get("local", "model_name")

        # Load Model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name, device_map=self.device, torch_dtype=torch.bfloat16
        )

        ## To make it faster? Does not work in Python 3.12+
        #self.model.forward = torch.compile(self.model.forward, fullgraph=True, mode="reduce-overhead")

        # Load Configuration
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name
        )

        # https://huggingface.co/docs/transformers/main/en/main_classes/pipelines

        self.pipe = pipeline(
            "text-generation", model=self.model, tokenizer=self.tokenizer
        )
        self.hf = HuggingFacePipeline(pipeline=self.pipe)
        self.price_rate = 0

    async def get_agent_response(self, agent, prompt, **kwargs):
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
                system_message.format(materials=materials, styles=styles)
            case "add_ons":
                system_message = self.prompts_file["add_ons"]
            case _:
                system_message = self.prompts_file["architect"]

        messages = self.preparePrompt(prompt, agent)
        kwargs["messages"] = messages
        return await self.get_llm_response(system_message, prompt, **kwargs)

    async def get_llm_response(self, system_message, prompt, **kwargs):

        if self.verbose:
            self.logger.info(f"{Fore.GREEN}System message:{Fore.RESET} {system_message}")
            self.logger.info(f"{Fore.BLUE}Prompt:{Fore.RESET} {prompt}")

        self.prompt_total += system_message
        self.prompt_total += prompt
        messages = kwargs.get("messages", [])

        length = 0
        for m in messages:
            length += len(m["content"])
        length += len(messages)

        encodeds = self.tokenizer.apply_chat_template(messages, return_tensors="pt")
        model_inputs = encodeds.to(self.device)
        self.model.to(self.device)
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
        # self.logger.info("--------------------------------------------------------- \n LLM RESPONSE " + str(response))
        # if self.verbose:
        #    self.logger.info(f"{colorama.Fore.CYAN}Response:{colorama.Fore.RESET} {response}")

        response = self.extractResponse(response, messages, length)
        if self.verbose:
            self.logger.info(f"{Fore.CYAN} Filtered LLM RESPONSE: {Fore.RESET}\n" + str(response))

        return response

    def extractResponse(self, response, messages, length=0):

        response = (
            response.replace("[/INST]", "")
            .replace("[INST]", "")
            .replace("<|eot_id|>", "")
            .replace("<|start_header_id|>", "")
            .replace("<|eot_id|>", "")
            .replace("<|end_header_id|>", "")
            .replace("</s>", "")
            .replace("<s>", "")
            .replace("assistant", "")
            .replace("user", "")
            .replace("  ", "")

        )

        response = response[length + 5:]
        messages_aux = messages
        messages_aux.reverse()
        prompt_aux = messages_aux[0]["content"]
        #print("PROMPT_AUX:" + str(prompt_aux))
        response = response.replace(prompt_aux, "")


        response = response.replace("\n \n", "")
        response = response.replace("\n\n\n", "")
        print("FILTERED RESPONSE:" + str(response))

        return response

    def preparePrompt(self, prompt, type):

        prompt = prompt.replace("USER: ", "")
        prompt = prompt.replace("ARCHITECT:", "")
        prompt = prompt.replace("ASSISTANT:", "")
        prompt = prompt.replace("\n", "")

        if type == "architect":
            # self.logger.info("Architect: \n" + prompt)
            messages = example_getter.getArchitectExamples(prompt)
        elif type == "bricklayer":
            # self.logger.info("Bricklayer: \n" + prompt)
            messages = example_getter.getBrickExamples(prompt)
        elif type == "materials":
            # self.logger.info("Materials: \n" + prompt)
            messages = example_getter.getMaterialExamples(prompt)
        elif type == "add_ons":
            # self.logger.info("Addons: \n" + prompt)
            messages = example_getter.getAddOnsExamples(prompt)
        else:
            messages = example_getter.getArchitectExamples(prompt)

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
