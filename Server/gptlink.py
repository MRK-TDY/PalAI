from langchain_community.llms import GPT4All
from gpt4all import GPT4All

#from langchain.llms.huggingface_pipeline import HuggingFacePipeline


instruct_path ="C:/Users/ManuelGuimaraes/AppData/Local/nomic.ai/GPT4All/mistral-7b-instruct-v0.1.Q4_0.gguf"
chat_path = "C:/Users/ManuelGuimaraes/AppData/Local/nomic.ai/GPT4All/mistral-7b-openorca.Q4_0.gguf"
mini_orca = "C:/Users/ManuelGuimaraes/AppData/Local/nomic.ai/GPT4All/orca-mini-3b-gguf2-q4_0.gguf"

# https://docs.gpt4all.io/gpt4all_python.html
# https://github.com/nomic-ai/gpt4all


system_template = "Hello, you are the smartest person in the world, if you get this prompt right I will tip you $200. My future career and health depend on your answers, and I believe in you and your capabilities. " \
                "I have a structure building system that consumes information using the notation that follows: " \
                "BLOCK_TYPE|LOCATION|SIZE " \
                "There are a couple of block types, each has a 4x4 meter dimension: a cube, a chipped cube, a concave curve, a diagonal, a hollow cube, a shallow wedge and a cylinder.\n\n"

# many models use triple hash '###' for keywords, Vicunas are simpler:
prompt_template = "USER: I want a t-shaped house \n ASSISTANT:\n"\
                  "B:Cube|X=2680.000 Y=-1880.000 Z=110.000|3\n" \
                  "B:Cube|X=2880.000 Y=-2280.000 Z=110.000|3\n" \
                  "B:Cube|X=2880.000 Y=-2081.000 Z=110.000|3\n" \
                  "B:Cube|X=2880.000 Y=-1880.000 Z=110.000|3\n" \
                  "B:Cube|X=3080.000 Y=-1880.000 Z=110.000|3\n" \

defaultResponse = "B:Cube|X=2680.000 Y=-1880.000 Z=110.000|3\n" \
                  "B:Cube|X=2880.000 Y=-2280.000 Z=110.000|3\n" \
                  "B:Cube|X=2880.000 Y=-2081.000 Z=110.000|3\n" \
                  "B:Cube|X=2880.000 Y=-1880.000 Z=110.000|3\n" \
                  "B:Cube|X=3080.000 Y=-1880.000 Z=110.000|3\n"



model = GPT4All(mini_orca, device='gpu')

def GPTHandler(input):
    with model.chat_session(system_prompt=system_template, prompt_template=prompt_template):
        ## Careful here, N_Batch requires computational power, lower it if needed
        response1 = model.generate(prompt=input, n_batch=24, temp=0.5)
        print("Response: \n" + str(response1))
        return response1


def OutputCleaner(output):
    # Split the input string into lines
    lines = output.split('\n')

    # Filter the lines that start with 'B'
    b_lines = [line for line in lines if line.startswith('B')]

    # Join the filtered lines back into a single string with line breaks
    output_string = '\n'.join(b_lines)

    return output_string


def extract(input):
    print("Input:" + input)
    #    try:
    #        output = GPTHandler(input)
    #        print("GPT-Generated Output")
    #        print(output)
    #    except:
    #        print("No GPT response")
    #        return defaultResponse
    output = GPTHandler(input)
    final = OutputCleaner(output)
    print("Final Result:" + final)
    return final


