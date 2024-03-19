

baseline = {
    "I want a tiny house":
        [{'type': 'CUBE', 'position': '(0,0,1)'}]
}



def evaluate(prompt, output):

    if prompt in baseline.keys():
        current_baseline_blocks = baseline[prompt]
        max_score = len(current_baseline_blocks)
        current_score = 0

        for block in current_baseline_blocks:
            if block in output:
                current_score += 1

        print("Output Score: " + str(current_score) + "/" + str(max_score))
        return current_score/max_score

    else:
        print("Output Evaluator: Prompt not in baseline list")

