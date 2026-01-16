---
name: build-plan
description: Use this to help formulate or re-build a research plan, or update its steps, etc
---

# build-plan Skill

A plan of research action is governed by a goal. The given goal is accomplished with a number of steps. Those steps and what we are allowed to do in the steps is subject to constraints.

The plan template can be found in this skill in `assets/plan-template.md` and if being created for the first time should be copied into the main repo and called `{goal-title}.md` where the name comes from the pity title (no spaces in the filename!).

## Context Snapshot

This is a scratch pad that keeps the important context about the work between sub-goals. At the end of each sub-goal, rewrite this section. It should contain enough information so that if you lost all your context nothing important would be lost.

## Constraints Section

These are things you should always follow when executing the goals. For example, if there is a certain way you should always run the code (with some flags), or if you should always make sure to read a particular file, etc.

There is one constraint there, which is instructing your to always keep a log of what you are doing. It should be written into a markdown file with the same name as the plan file plus `-log` in the name.

## Hints

The hints section contains helpful things you discover while executing the plan. For example, a particular command takes much longer to run than you might expect (e.g. dealing with timeouts).

## Sub-Goals

This is the most important section - a list of sub-goals to acheive the overall goal. Because all the sub-goals to obtain the goal aren't always understood at first, the sub-goals may not be complete.

Goals are failry high level and include multiple steps (running code to get a result, modifying the code, iterating, etc.). If you are exploring towards a soluiton, for example, a sub-goal may be exploring a possible modification towards the solution, and testing that modification. The end of the sub-goal may be to abandon that approach, or that something further is needed.

A completed sub-goal is marked with the `**Acheived**` text.

## Steps

The step section should be setup with the next sub-goal to be acheived, and some initial steps. It is always given that the steps can evolve as we learn more about making our way towards the goal.

The section should be written as in the template. When first setting the plan up, feel free to just leave the template text there.

## Future Ideas

  This part of the plan is a scratch pad for possible ideas to examine in the future. Think of it like a combination of a todo list and also possible avenues to explore. Not everything here should be explored!
  