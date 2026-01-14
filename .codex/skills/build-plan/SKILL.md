---
name: build-plan
description: Use this to help formulate or re-build a research plan, or update its steps, etc
---

# build-plan Skill

A plan of research action is governed by a goal. The given goal is accomplished with a number of steps. Those steps and what we are allowed to do in the steps is subject to constraints.

The plan template can be found in this skill in `assets/plan-template.md` and if being created for the first time should be copied into the main repo and called `{goal-title}.md` where the name comes from the pity title (no spaces in the filename!).

## Constraints Section

These are things you should always follow when executing the goals. For example, if there is a certain way you should always run the code (with some flags), or if you should always make sure to read a particular file, etc.

There is one constraint there, which is instructing your to always keep a log of what you are doing. It should be written into a markdown file with the same name as the plan file plus `-log` in the name.

## Hints

The hints section contains helpful things you discover while executing the plan. For example, a particular command takes much longer to run than you might expect (e.g. dealing with timeouts).

## Steps

This is the most important section - a list of steps in the plan. Because all the steps to obtain the goal aren't always understood at first, the steps may not be complete.

As each step is completed:
    - The step should be marked "**done**`.
    - Write a short description of the result. It should be detailed enough so that if you go back and re-read this you can figure out the result without having to repeat the work fo the step.
    - Examine the next step(s) in in light of the results from this step. If they don't make sense, remove them.
    - If there is no next step, then author a new one.

Writing new steps:

- First determine what is the next logical step to get to the goal.
- Look at the future ideas section to see if there are any better ideas there.
- If you have some other ideas, feel free to write them into the future ideas section.
- The step should be written as a high-level thing
  - don't talk about modifying specific files
  - Do talk about the general changes you'd like to make
  - Or talk about the tests that you want to run
  - Or talk about the data you'd like to get in order to make a decision.
  - The steps should be specific (add the capability x, or collect data for y).
  - Use active verbs when describing the steps.

Unless the user has told you otherwise, after adding new steps to the plan, check with them before executing them.

## Future Ideas

  This part of the plan is a scratch pad for possible ideas to examine in the future. Think of it like a combination of a todo list and also possible avenues to explore. Not everything here should be explored!
  