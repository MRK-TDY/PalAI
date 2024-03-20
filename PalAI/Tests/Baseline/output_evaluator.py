

baseline = {
    "I want a tiny house":
        [{'type': 'CUBE', 'position': '(0,0,0)'},
         {'type': 'CUBE', 'position': '(0,0,1)'},
         {'type': 'CUBE', 'position': '(1,0,1)'},
         {'type': 'CUBE', 'position': '(1,0,0)'}],
    "I want a tiny modern house":
        [{'type': 'DIAGONAL', 'position': '(0,0,0)', 'rotation': 0},
         {'type': 'DIAGONAL', 'position': '(0,0,1)', 'rotation': 1},
         {'type': 'DIAGONAL', 'position': '(1,0,1)', 'rotation': 2},
         {'type': 'DIAGONAL', 'position': '(1,0,0)', 'rotation': 3}],

    "I want a tiny 2-floor house":
        [{'type': 'CUBE', 'position': '(0,0,0)'},
         {'type': 'CUBE', 'position': '(0,0,1)'},
         {'type': 'CUBE', 'position': '(1,0,1)'},
         {'type': 'CUBE', 'position': '(1,0,0)'},
         {'type': 'CUBE', 'position': '(0,1,0)'},
         {'type': 'CUBE', 'position': '(0,1,1)'},
         {'type': 'CUBE', 'position': '(1,1,1)'},
         {'type': 'CUBE', 'position': '(1,1,0)'}],

    "I want a 1-floor modern house":
    [{'type': 'DIAGONAL', 'position': '(0,0,0)', 'tags': {'type': 'DOOR', 'position': '(1,0,0)'}, 'rotation': 2}, {'type': 'CUBE', 'position': '(0,0,1)', 'tags': {'type': 'WINDOW', 'position': '(1,0,1)'}}, {'type': 'CUBE', 'position': '(0,0,2)', 'tags': {'type': 'WINDOW', 'position': '(1,0,2)'}}, {'type': 'CUBE', 'position': '(0,0,3)', 'tags': {'type': 'WINDOW', 'position': '(1,0,3)'}}, {'type': 'DIAGONAL', 'position': '(0,0,4)', 'tags': {'type': 'DOOR', 'position': '(1,0,4)'}, 'rotation': 1}, {'type': 'CUBE', 'position': '(1,0,0)', 'tags': {'type': 'WINDOW', 'position': '(2,0,0)'}}, {'type': 'CUBE', 'position': '(1,0,1)'}, {'type': 'CUBE', 'position': '(1,0,2)'}, {'type': 'CUBE', 'position': '(1,0,3)'}, {'type': 'CUBE', 'position': '(1,0,4)', 'tags': {'type': 'WINDOW', 'position': '(2,0,4)'}}, {'type': 'CUBE', 'position': '(2,0,0)', 'tags': {'type': 'WINDOW', 'position': '(3,0,0)'}}, {'type': 'CUBE', 'position': '(2,0,1)'}, {'type': 'CUBE', 'position': '(2,0,2)'}, {'type': 'CUBE', 'position': '(2,0,3)'}, {'type': 'CUBE', 'position': '(2,0,4)', 'tags': {'type': 'WINDOW', 'position': '(3,0,4)'}}, {'type': 'CUBE', 'position': '(3,0,0)', 'tags': {'type': 'WINDOW', 'position': '(4,0,0)'}}, {'type': 'CUBE', 'position': '(3,0,1)'}, {'type': 'CUBE', 'position': '(3,0,2)'}, {'type': 'CUBE', 'position': '(3,0,3)'}, {'type': 'CUBE', 'position': '(3,0,4)', 'tags': {'type': 'WINDOW', 'position': '(4,0,4)'}}, {'type': 'DIAGONAL', 'position': '(4,0,0)', 'tags': {'type': 'DOOR', 'position': '(3,0,0)'}, 'rotation': 3}, {'type': 'CUBE', 'position': '(4,0,1)', 'tags': {'type': 'WINDOW', 'position': '(4,0,1)'}}, {'type': 'CUBE', 'position': '(4,0,2)', 'tags': {'type': 'WINDOW', 'position': '(4,0,2)'}}, {'type': 'CUBE', 'position': '(4,0,3)', 'tags': {'type': 'WINDOW', 'position': '(4,0,3)'}}, {'type': 'DIAGONAL', 'position': '(4,0,4)', 'tags': {'type': 'DOOR', 'position': '(3,0,4)'}, 'rotation': 0}]
}



def evaluate(prompt, output):

    if prompt in baseline.keys():
        current_baseline_blocks = baseline[prompt]
        max_score = len(current_baseline_blocks)
        current_score = 0

        for block in current_baseline_blocks:
            if block in output:
                current_score += 1

        print("Quality of Output Score: " + str(current_score) + "/" + str(max_score))
        return current_score/max_score

    else:
        print("Output Evaluator: Prompt not in baseline list")

