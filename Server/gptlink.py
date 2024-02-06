from gpt4all import GPT4All
import yaml

# https://docs.gpt4all.io/gpt4all_python.html
# https://github.com/nomic-ai/gpt4all

class GPTHandler():
    def __init__(self, config):
        self.model = GPT4All(config.get('llm', 'chat_path'), device='gpu')
        self.n_batch = config.getint('llm', 'n_batch')
        self.temp = eval(config.get('llm', 'temp'))
        self.prompt_template = 'USER: {0}\nASSISTANT: '

        with open(config.get('llm', 'prompts_path'), 'r') as file:
            self.prompts_file = yaml.safe_load(file)
        self.system_prompt = self.prompts_file['system_prompt']

    def get_llm_response(self, prompt):
        with self.model.chat_session(system_prompt=self.system_prompt, prompt_template=self.prompt_template):
            ## Careful here, N_Batch requires computational power, lower it if needed
            response = self.model.generate(prompt=prompt, n_batch=self.n_batch, temp=self.temp)
            print("Response: \n" + str(response))
            return response

    def get_building_data(self, prompt):
        response = self.get_llm_response(prompt)

        # extract building information from prompt
        building_info = self.extract_building_information(response)
        # convert into UE-ready format

        return building_info


    def extract_building_information(self, text):
        lines = text.split('\n')
        building_info = []

        # match lines that have two `|` characters
        for line in lines:
            if line.count('|') == 2:
                building_info.append(line)

        return building_info

    # def OutputCleaner(self,output):
    #     # Split the input string into lines
    #     lines = output.split('\n')
    #
    #     # Filter the lines that start with 'B'
    #     b_lines = [line for line in lines if line.startswith('B')]
    #
    #     # Join the filtered lines back into a single string with line breaks
    #     output_string = '\n'.join(b_lines)
    #
    #     return output_string


    # def extract(self, input):
    #     print("Input:" + input)
    #     output = GPTHandler(input)
    #     final = OutputCleaner(output)
    #     print("Final Result:" + final)
    #     return final
