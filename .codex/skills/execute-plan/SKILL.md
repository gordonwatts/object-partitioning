---
name: execute-plan
description: The user wants to follow the steps in a plan to drive it towards its goal
---
# Execute Plan

The user should specify which plan file they want to use. If they have not, make sure to ask them - everything is going to

## Workflow

1. Read the plan file, and read the log file that is referenced in the plan file (you may need only to read the bottom part of the log file).
2. Develop a plan to execute the next step in the plan.
3. Execute those steps, making sure to update the log.
4. If you can't complete the step for some reason
    - It could be the step is more complex than thought - feel free to rewrite the step into a series of sub-steps in the plan file, and then execute only the first step.
    - If there is a bigger problem, do not hesitate to ask the user for input and guidance.
5. Once the step is done, mark it as `**Done**`, add a short `Result:` line below the step. This should contain enough information that you do not need to re-run the step if you were reading the text cold to understand what the current state and results were.
6. Inspect the next step and see if it still makes sense given these new results. If so, then leave it. Otherwise remove it.
7. Make sure there is a sensible next step
    - Consider the best three different things to do as the next step that will help get you to the goal.
    - Choose the best one and write it down as the next step. If the other two are good - add them to the `Future Ideas` section of the plan.
8. Let the user know the results and what the next step is and wait to see what they want to do before moving on.
