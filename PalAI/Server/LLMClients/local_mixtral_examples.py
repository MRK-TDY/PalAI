
def getArchitectExamples(prompt):
    user = [""]
    assistant = [""]
    messages = []
    example1_user = "I want to build a house that widens at the top."

    example1_assistant = "In order to build a house that widens at the top we must place 3 square shapes on top of each other.\n \
  Layer 0: A square shape 4 blocks wide.\n \
  Layer 1: Here we repeat the last layer, placing again a square shape 4 blocks wide.\n \
  Layer 2: We widen the shape according to the user request.\n"

    messages.append({"role": "user", "content": example1_user})
    messages.append({"role": "assistant", "content": example1_assistant})

    example2_user = "I want to build an L-shaped house."

    example2_assistant = "In order to build an L shaped house we must place 4 square shapes on the ground, there's no need for other layers.\n \
  Layer 0: 4 blocks in a row from to form the long side of the L shape, with 2 blocks at the end in an angle to form the short side.\n"

    messages.append({"role": "user", "content": example2_user})
    messages.append({"role": "assistant", "content": example2_assistant})

    example3_user = "I want to build a pyramid."

    example3_assistant = "In order to build a pyramid, we will create a structure that narrows as it goes up, resulting in a pointed top.\n \
  Layer 0: A square shape 5 blocks wide on each side to serve as the base. \n \
  Layer 1: A smaller square shape, 3 blocks wide, centered on top of the previous layer.\n \
  Layer 2: A single block centered on top of the previous layer.\n"

    messages.append({"role": "user", "content": example3_user})
    messages.append({"role": "assistant", "content": example3_assistant})

    example4_user = "I want to build a tower with a balcony."

    example4_assistant = "In order to build a tower with a balcony, we will create a tall structure with an extending section on one side.\n\
  Layer 0: A square shape 3 blocks wide on each side to form the base of the tower.\n\
  Layer 1: Repeat the same square shape 3 blocks wide to continue the tower's structure.\n\
  Layer 2: Create a square shape 3 blocks wide for the tower, and extend a row of blocks out on one side to form the balcony.\n"

    messages.append({"role": "user", "content": example4_user})
    messages.append({"role": "assistant", "content": example4_assistant})

    messages.append({"role": "user", "content": prompt})

    return messages

def getBrickExamples(prompt):
    user = [""]
    assistant = [""]
    messages = []
    example1_user = "Create an L-shaped house flat on the ground."

    example1_assistant = "To create an L-shaped house we will create a row of 4 cubes" \
                         " along the X-axis, from points (0,0) to (4,0), followed by 2 cubes at the end, " \
                         "placed perpendicularly, along the y-axis, from (0,0) to (0,2). First the long side:\n \
  B:CUBE|0,0\n\
  B:CUBE|1,0\n\
  B:CUBE|2,0\n\
  B:CUBE|3,0\n\
  Then the short side:\n\
  B:CUBE|0,1\n\
  B:CUBE|0,2\n"

    messages.append({"role": "user", "content": example1_user})
    messages.append({"role": "assistant", "content": example1_assistant})

    example2_user = "Create an H-shaped house flat on the ground."

    example2_assistant = "To create an H-shaped house we will create 2 rows of 3 cubes and one in the midle with just one cube. " \
                         "  Let's start with the first leg:\n\
      B:CUBE|0,0\n\
      B:CUBE|1,0\n\
      B:CUBE|2,0\n\
      Then the second leg:\n\
      B:CUBE|0,2\n\
      B:CUBE|1,2\n\
      B:CUBE|2,2\n\
    Then the bridge between them:\n\
      B:CUBE|1,1\n"

    messages.append({"role": "user", "content": example2_user})
    messages.append({"role": "assistant", "content": example2_assistant})

    example3_user = "I want to 2 block square house"

    example3_assistant = "To create a 2 block square house we can create 2 by 2 blocks starting on the 0,0 \n \
  B:CUBE|0,0\n\
  B:CUBE|1,0\n\
  B:CUBE|0,1\n\
  B:CUBE|1,1\n"

    messages.append({"role": "user", "content": example3_user})
    messages.append({"role": "assistant", "content": example3_assistant})

    example4_user = "I want to 4 block square house"

    example4_assistant = "To create a 4 block square house we can create 4 by 4 blocks starting on the 0,0 \n \
  B:CUBE|0,0\n\
  B:CUBE|1,0\n\
  B:CUBE|2,0\n\
  B:CUBE|3,0\n\
  B:CUBE|0,1\n\
  B:CUBE|1,1\n\
  B:CUBE|2,1\n\
  B:CUBE|3,1\n\
  B:CUBE|0,2\n\
  B:CUBE|1,2\n\
  B:CUBE|2,2\n\
  B:CUBE|3,2\n\
  B:CUBE|0,3\n\
  B:CUBE|1,3\n\
  B:CUBE|2,3\n\
  B:CUBE|3,3\n"

    messages.append({"role": "user", "content": example4_user})
    messages.append({"role": "assistant", "content": example4_assistant})

    messages.append({"role": "user", "content": prompt})

    return messages


def getMaterialExamples(prompt):
    user = [""]
    assistant = [""]
    messages = []

    system_message = "Pick from the following materials and styles:\n\
Materials: Plastic Orange, Concrete White, Metal Blue, Metal Dark Blue, Honeycomb White, Grey Light Wood«, Concrete Grey \
Concrete Dark Stripes Blue, Marble, Dark Marble, Sand, Dark Red, Molten Marble, Plastic Red, Stone Light Grey, Dark Concrete\n" \
                    "Styles: modern, gotchic, normal, rounded"

    example1_user = "I want a modern house. \n" + system_message

    example1_assistant = "Floor:Concrete White\n\
  Interior: Metal Blue\n\
  Exterior: Marble\n\
  Style: modern\n"

    messages.append({"role": "user", "content": example1_user})
    messages.append({"role": "assistant", "content": example1_assistant})

    example2_user = "I want square block house.\n" + system_message

    example2_assistant = "Floor:Concrete White\n\
      Interior: Metal Dark Blue\n\
      Exterior: Stone Light Grey\n\
      Style: normal\n"

    messages.append({"role": "user", "content": example2_user})
    messages.append({"role": "assistant", "content": example2_assistant})

    example3_user = "I want a rounded house.\n" + system_message

    example3_assistant = "Floor: Metal Blue\n\
         Interior: Marble\n\
         Exterior: Molten Marble\n\
         Style: rounded\n"

    messages.append({"role": "user", "content": example3_user})
    messages.append({"role": "assistant", "content": example3_assistant})

    messages.append({"role": "user", "content": prompt})

    return messages


def getAddOnsExamples(prompt):

    messages = []
    example1_user = "Your job is to take the existing building and add doors and windows to it.\n \
      Here is the syntax of the code that creates the buildings:\n  B:BLOCK_TYPE|LOCATION|LAYER|ADD-ON.\n" \
                    "Create a block with no windows at point 0,0\n" \
                    "B:CUBE|0,0|0"

    example1_assistant = "B:CUBE|0,0|0"


    messages.append({"role": "user", "content": example1_user})
    messages.append({"role": "assistant", "content": example1_assistant})

    example2_user = "Create a cube at the point 2,3, on the 1st layer (meaning above the other layer). " \
                    "We then add a window to this block, facing the point 2,2.\n" \
                    "Here is the building with no windows or doors\n" \
                    "B:CUBE|0,0|0\n"\
                    "B:CUBE|0,0|1\n" \
                    "B:CUBE|0,0|2\n" \

    example2_assistant = "B:CUBE|0,0|1|WINDOW|0,0"

    messages.append({"role": "user", "content": example2_user})
    messages.append({"role": "assistant", "content": example2_assistant})

    example3_user = "Here is the building with no windows or doors\n" \
                    "B:CUBE|0,0|0\n" \
                    "B:CUBE|1,0|0\n" \
                    "B:CUBE|0,1|0\n" \
                    "B:CUBE|1,1|0\n" \
                    "B:CUBE|1,1|1\n" \
                    "B:CUBE|1,0|1\n"

    example3_assistant = "B:CUBE|0,0|0|DOOR|0,0\n" \
                         "B:CUBE|1,1|1|WINDOW|0,0"

    messages.append({"role": "user", "content": example3_user})
    messages.append({"role": "assistant", "content": example3_assistant})

    example4_user = "Create a door in the middle of the house.\n" \
                    "B:CUBE|0,0\n\
                    B:CUBE|1,0\n\
                    B:CUBE|0,1\n\
                    B:CUBE|1,1"

    example4_assistant = "B:CUBE|0,0|0|DOOR|0,0"

    messages.append({"role": "user", "content": example4_user})
    messages.append({"role": "assistant", "content": example4_assistant})

    messages.append({"role": "user", "content": prompt})

    return messages