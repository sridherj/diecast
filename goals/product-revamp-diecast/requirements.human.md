Goal:
Create a mock up version of Diecast that will represent my vision so that I can start executing my vision. There are quite a few open ended ideas I want to explore/refine and then create this mock up version.

Target Users:
Primary: Eng
Secondary: PM (either now or future, but it should be extensible)

Principles:
- Ensure we identify different workflows and start optimizing each of them.
- Keep questioning ourselves if we are thinking from first principles.
- Fluid design is something we should aim for - combination of chat + ui directiontional nudges - may have to find some inspiration from other tools. In other words, user always has control to change direction, but we do interesting defaults as well in product
- don't be constrained with what we have so far

Vision:
- early version of my vision - file:///data/workspace/second-brain/taskos/goals/taskos-gtm/presentation_v3/ ;
-  ~/workspace/second-brain/ may have more ideas that I have discussed in the past around this

Reference:
- /data/workspace/diecast/goals/revamp-diecast/requirements.human.md
- /home/sridherj/workspace/diecast/goals/refine-requirements-v2/requirements.human.md

Top of mind thoughts:
- Simple setup on mac/windows/linux; copilot/claude/codex shouldn't matter (not sure if this has any effect on vision, just adding)
- Grill me on this, but I was thinking something like a chat interface + fluid UI that will guide me thru next steps. eg: today we have requirements -> exploration -> planning -> execution. For most parts this may be the right start, but things may be very diff for requirements for a bug fix vs user facing feature. Another example - for debugging you may go thru multiple hypothesis->experiment->observation-> iterations. showing that in other ways is not useful. I am not sure if the tabs need to change, but saying we should definitely think what would be the best user experience? Today its very tight. It should be representing a software built for future. Chat guidance could change what's shown in the UI (if user decides to change course/intent). Get enough inspirations first as assets or videos from internet.
- /home/sridherj/workspace/diecast/goals/refine-requirements-v2/requirements.human.md has some points around the projects I have done earlier which have writeups/requirements to help you get some diff workflows. You can do more research online as well. Is it worht making these workflows top class citizens?
- Current diecast ui also gives some idea
- Skillification, agent usage/metrics around it, monitoring etc r useful. agent version is also important.
- Private skills should be diff from company wide skills and we should provide very easy ways to create them. could just end up as claude command...
- Agent assessments, hiring is also an interesting aspect. eg: I am working on a project and I want to hire rbac-agent. I will ask claude to create an assessment for an rbac-agent hire across few diff tasks based on your products dimension (few users, large user base, internal software/external software...), federate it to 5-10 diff rbac-agents and analyze their output and come up with a google style hiring report stackranked with pros/cons. User can hire an agent first and then onboard (pointing to your data sources, tastes etc).
- Agents also advertise their usage/credibility (apify like). eg: 99.9% compliance code in 2 maker-checker loops across 505 runs. Take a look at the same code created (repo link).
- Around the fluidity point - a user may go thru things multiple iterations; we should support those flows cleanly.
- Spike tasks can be made first class citizens as they help come to conclusions very quickly in the product.
- Useful reference: /data/workspace/diecast/goals/refine-requirements-v2/refined_requirements.collab.md
- Useful repos: ~/workspace/reference_repos (you may want to do git pull on some of them)

Added during refinement (2026-06-11):
- We are slowly moving towards WHAT as primary and important details on HOW mode with AI development (AI does most of the execution and to some extent keeps it as a blackbox - so our product should be reflective of that at top level with ability to get more details 'execution tab'). This is primarily because of increased capability from claude workflow/goal types.
- Testing is a critical part as it's the outcome of 'WHAT'. So we should think how to best show the output - screenshots/data visualization/html output ...

Decision Tracking [New addition]
- I think one of the aspects is to track decisions at various phases - we should keep track of them, clarify with users whenever required depending upon the autonomy users expect and document/surface them at right places in product along with rationale/time etc. 
