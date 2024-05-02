
import json
import os

def getArchitectExamples(prompt):

    with open(os.path.join(os.path.dirname(__file__), 'prompt_examples.json'), 'r', encoding='utf-8') as f:
        # returns JSON object as
        # a dictionary
        jsondata = json.load(f)
        messages = []
        for data in jsondata["architect_examples"]:
            messages.append({"role": "user", "content": jsondata["architect_examples"][data]["user"]})
            messages.append({"role": "assistant", "content": jsondata["architect_examples"][data]["assistant"]})

        messages.append({"role": "user", "content": prompt})
        return messages

def getBrickExamples(prompt):
    # Opening JSON file

    with open(os.path.join(os.path.dirname(__file__), 'prompt_examples.json'), 'r', encoding='utf-8') as f:
        # returns JSON object as
        # a dictionary
        jsondata = json.load(f)
        messages = []
        for data in jsondata["bricklayer_examples"]:
            messages.append({"role": "user", "content": jsondata["bricklayer_examples"][data]["user"]})
            messages.append({"role": "assistant", "content": jsondata["bricklayer_examples"][data]["assistant"]})

        messages.append({"role": "user", "content": prompt})
        return messages


def getMaterialExamples(prompt):
    with open(os.path.join(os.path.dirname(__file__), 'prompt_examples.json'), 'r', encoding='utf-8') as f:
        # returns JSON object as
        # a dictionary
        #jsondata = json.load(f)
        messages = []
        #for data in jsondata["house_design_examples"]:
        #    messages.append({"role": "user", "content": jsondata["house_design_examples"][data]["user"]})
        #    messages.append({"role": "assistant", "content": jsondata["house_design_examples"][data]["assistant"]})

        messages.append({"role": "user", "content": prompt})
        return messages



def getAddOnsExamples(prompt):
    with open(os.path.join(os.path.dirname(__file__), 'prompt_examples.json'), 'r', encoding='utf-8') as f:
        # returns JSON object as
        # a dictionary
        jsondata = json.load(f)
        messages = []
        for data in jsondata["addons_examples"]:
            messages.append({"role": "user", "content": jsondata["addons_examples"][data]["user"]})
            messages.append({"role": "assistant", "content": jsondata["addons_examples"][data]["assistant"]})

        prompt = prompt.replace("B:", "\nB:")
        messages.append({"role": "user", "content": prompt})
        return messages
