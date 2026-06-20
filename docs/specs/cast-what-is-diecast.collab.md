What is DieCast?
- Cockpit to get work done through 100s of AI agents (claude sub-agents type) delivering deterministic output (or close to it) - takes care of monitoring, feedback loops, quality control, reuse, memory, planning and execution
- It works on top of claude code/cli version of codex/cursor/copilot

Users:
- Non-tech & Tech folks who use tools like claude (cowork or code)/codex/copilot

Disambiguation of word AI agent:
One of the most overloaded word today on internet is AI agent 
- AgentType1: it could mean AI agents that make a bunch of LLM calls to achieve something (similar to a program except it is non-deterministic)
- AgentType2: it could mean the claude code sub-agents type AI agent that reside inside .claude/agents/ folder. 
We are talking about (2).

Context:
- Though a lot of users are using AI tools to do their work, they haven't internalized workflows to get the best out of AI. Lot of folks still have very long conversations with AI without understanding context management, value of persistence, avoiding duplicate work by creating agents etc.
- Skillification (or creation of AI agents) is going to be one key leverage of organizations to get the best out of AI tools - doing same tasks repeatedly with frontier models is both slow and costly
- Most of the agent harnesses have been focussing on coding - like plan, build, test cycles. While that is the first step, future harnesses could change shape significantly - when you start thinking about assessing, hiring & managing 1000s of agents, agent observability (not langfuse type which works with AgentType1), getting deterministic outcomes from agents, interventions/feedback, we are talking about a new world where AI agents behave like human employees and humans just orchestrate them to get things done!

Vision:
Humans in lean organizations orchestrating large number of tasks in parallel across board leveraging lots of battle-tested personal (user level), private (org level) and public AI agents getting deterministic output.
- human-taste & org context baked in (personal/private skills + docs/ type context, HITL)
- close to deterministic output (agent maker/checker, agent assessment and hiring, agent evals)
- layered visibility to guide AI agents. Surfacing 
-- decisions
-- escalations/open-questions
-- trajectory & deviations
-- milestones & artifacts
-- proof points
-- right HITL mechanics
- agent-first planning & execution
-- deterministic output = deterministic expectation - In other words, expectation on requirements/outcomes has to be explicit without ambiguity
-- workflow based fluid UI
-- intelligent defaults with more levers for power users
-- agent tools & data connectors
- agent lifecycle management
-- agent creation, output quality & evals
-- expertise leveraged from specialists (public agents to hire with resume)
-- agent performance tracking ($ spend, mistakes made, # of maker-checker loops, time metrics, learning rate, runs)
-- learning loops (memory/self-learning through corrections, HITL)
-- audit trail 

Product Principles:
- Prioritize human consumption/time: Avoid AI slop in every single communication with user - could be plan, requirements, test results - anything. Leveraging HTML/CSS with right design constructs may help here (see /cast-refine-requirements).
- Progressive Disclosure - Ruthlessly push down items in the information hierarchy; 
Analogy: Treating agent hierarchy as org hierarchy is a great way to get this right. CEO will not talk to QA person to get updates - but can always ask for more or less info about any project. At each level, appropriate level of details should be visible.
- Establishing Trust: Overall design should establish human trust at every point helping them clearly understand what AI will deliver. It can manifest in the product in several ways - few examples:
-- showing a small prototype before building something
-- recommending spike tasks to get critical answers faster instead of getting stuck 5 levels deep down
-- where possible, show how output will look like to clarify expectations
-- showing logged decisions/impact
-- right escalations with clear context and easy to approve/disprove
-- getting WHAT can be as interactive as possible so that we don't waste tokens/time in how


- Composability

v0 prototype (incomplete, just made to fine tune thoughts): ~/workspace/scratchpad/prototype/index.html

Rough Notes to be expanded:
- Artifacts being the guidance factor - guide the user using an agent!
- guiding-agent - determines artifacts, flows, intent and keeps readjusting. typically based on flow, there are a set of sub-agents it needs to \
use. there will be one guiding subagent who will take the user throughout the journey. it will decide the intent of the user and decide which pa\
th to take. eg: if its bug fix, it may show certain things like repro, rca, evidence, potential fixes, fix, tests. if its new feature - requirem\
ents, prototype with choices to lock UI, locked design, eng design, execution, test reports. haven't thought thru these steps, but just saying t\
he guiding subagent (need to think of a better name) will be the one that will guide the user throughout the flow to get the best outcomes. at e\
ach step it keeps thinking what's the right next step and suggests users (sometimes even making pivots in between)
- maker/checker - agent definition. sometimes shared points may be in multiple agents. prompt injection? makers can also have multiple checkers.

- multiple runs on same project not working becaquse of some symlinkiing thing
- autonomous - low/med/high

- preview/prototype are very useful features

Reference:
(Split into insights / players / people. Full market research lives in goals/agent-harness-market-research/exploration/ — start at 00-SUMMARY.md; competitor watchlist in 08-watchlist.md; Dust profile in 09; skill-repo + insight verdicts in 10.)

INSIGHTS (read / learn from):
- Very useful - https://lexler.github.io/augmented-coding-patterns/pattern-catalog/, ~/workspace/reference_repos/augmented-coding-patterns  [cleanest taxonomy of agent patterns/anti-patterns/obstacles; the prototype's decision records = its "Decision Guards" pattern]
- Thoughtworks "harness engineering" cluster — literally our category name:
  -- Spec-Driven Development: https://www.thoughtworks.com/insights/blog/agile-engineering-practices/spec-driven-development-unpacking-2025-new-engineering-practices  [specs guide, code stays source of truth, CI is the backstop]
  -- What is harness engineering? https://www.thoughtworks.com/insights/podcasts/technology-podcasts/what-harness-engineering
  -- AI coding sensors: https://www.thoughtworks.com/en-us/insights/blog/generative-ai/harness-engineering-agent-feedback-exploring-ai-coding-sensors  [skills drove H1-2026; "sensors" are the next under-built piece — relevant to our Sensors principle]
- https://www.eomag.io/article/stanford-mihail-eric  [Stanford, AI-native SDLC; orchestration + error-compounding is the skill; agent-friendly codebases = explicit contracts]
- Skill repos (verdicts in exploration/10):
  -- STUDY: obra/superpowers (composable skills + skill-authoring meta-skill + worktree isolation), addyosmani/agent-skills (phase-structured SDLC, multi-harness)
  -- PRIOR-ART CORPUS (caveat: leaked / GPL): x1xhlol/system-prompts-and-models-of-ai-tools
  -- STRUCTURAL REFERENCE ONLY: phuryn/pm-skills (skill-catalog shape), mvanhorn/last30days-skill (fan-out research skill)
  -- SKIP (not harness-relevant): refactoringhq/tolaria, harry0703/MoneyPrinterTurbo

PLAYERS (same market — tiered list in exploration/08-watchlist.md):
- https://dust.tt/ ; https://www.axios.com/pro/enterprise-software-deals/2026/05/18/agentic-ai-dust-snowflake-sequoia ; https://www.youtube.com/watch?v=01NYw3PzqiI  [Clear pivot, drives AI adoption — THE most direct competitor; same GTM; profile in 09]
- https://hyperagent.com/ ; https://www.youtube.com/watch?v=PYZJDx4qMMw  [non-dev agent teams; product demo]
- https://paperclip.ing/  [concept twin — run agents as a company; dev-only; cloned in reference_repos/paperclip]
- https://www.realfast.ai/  [enterprise agent delivery; services-heavy]
- https://kiro.dev/  [heavy on spec-driven development; Amazon; dev-IDE lane — validates spec-first thesis]
- guild.ai  [control plane for agents; $44M Series A]
- https://techcrunch.com/2026/03/12/gumloop-lands-50m-from-benchmark-to-turn-every-employee-into-an-ai-agent-builder/  [no-code agent builder]
- https://www.arcade.dev/  [agent tools + auth/OAuth layer — lets agents take real authenticated actions; the "agent tools & data connectors" infra lane]
- adjacent enterprise AI-adoption platforms (detail in 09): Glean, Sana/Workday, Cohere North, Writer; cross-harness OSS: omnigent (Databricks), gastown; certification: AIUC-1

PEOPLE TO FOLLOW (vetted list in exploration/06-people-sources.md):
- Builders: Anthropic Engineering blog, Birgitta Böckeler (Thoughtworks), Simon Willison, Hamel Husain (evals), Lance Martin, Cognition/Sourcegraph builders, lexler/Lada Kesseler, Addy Osmani, Jesse Vincent (obra), Mihail Eric (Stanford), Paweł Huryn (PM skills)
- Commentary: swyx/Latent Space, Eugene Yan

Unsure:
- Nap AI Inc.