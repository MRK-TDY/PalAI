import openai
import yaml

#with open("../config.yaml", "r") as f:
#    config = yaml.load(f, Loader=yaml.FullLoader)
#    openai.organization = config['openai_organization']
#    openai.api_key = config['openai_api_key']

StartSequence = "I am in need of a structure that recreates the house from the simpsons." \
                "In order to do this my building system takes information using the notation that follows: \n" \
                "BLOCK_TYPE|LOCATION|SIZE \n" \
                "Could you try to recreate " \



defaultResponse = "B:Cube|X=2680.000 Y=-1880.000 Z=110.000|3\n" \
                   "B:Cube|X=2880.000 Y=-2280.000 Z=110.000|3\n" \
                   "B:Cube|X=2880.000 Y=-2081.000 Z=110.000|3\n" \
                   "B:Cube|X=2880.000 Y=-1880.000 Z=110.000|3\n" \
                   "B:Cube|X=3080.000 Y=-1880.000 Z=110.000|3\n"


openai.api_key = "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"

def GPTHandler(input):

    completePrompt = StartSequence + "Player: " + input + "\n"

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user","content":completePrompt}]
    )

    return response['choices'][0]['text']

def extract(input):
    print(input)
#    try:
#        output = GPTHandler(input)
#        print("GPT-Generated Output")
#        print(output)
#    except:
#        print("No GPT response")
#        return defaultResponse
    output = GPTHandler(input)
    #print("Output: " + output)
    return output
