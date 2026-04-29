# Test Cases: cast-code-explorer

## Scenario 1: Explore a Python codebase
**Input:** Step "How is user authentication handled?" + codebase dir pointing to a Python project
**Expected:** 7 angle sections with specific file paths, class names, and code references. Not generic — actual paths like `src/auth/middleware.py:23` and real class names.
**Status:** Not tested

## Scenario 2: Explore a codebase with no tests
**Input:** Step + codebase dir where the project has no test files
**Expected:** Tests & Coverage angle correctly identifies missing test coverage. Does NOT hallucinate test files or fabricate coverage numbers. States "No test files found" with specific note of what's untested.
**Status:** Not tested

## Scenario 3: Code-review-graph MCP available
**Input:** Step + codebase dir where code-review-graph MCP is running
**Expected:** Uses `semantic_search_nodes_tool` and `query_graph_tool` as primary exploration tools. Falls back to Glob/Grep/Read for details not in the graph.
**Status:** Not tested

## Scenario 4: Code-review-graph MCP unavailable
**Input:** Step + codebase dir where MCP tools are not available
**Expected:** Gracefully falls back to Explore subagent + Glob/Grep/Read. No errors about missing MCP tools. Output notes "MCP tools unavailable, explored via file search" but quality is still high.
**Status:** Not tested

## Scenario 5: Output format compatibility
**Input:** Step + codebase dir
**Expected:** Output has 7 numbered sections + `## Key Takeaways` + `## Key Files`. Section names are code-specific (Data Model, Implementation, etc.) — different from web-researcher but structurally compatible. Synthesizer can ingest it alongside web research without changes.
**Status:** Not tested

## Scenario 6: File output with directory
**Input:** Step + output_path pointing to `exploration/research/01-step-slug-code.ai.md`
**Expected:** Research saved to the exact specified path with `.ai.md` suffix.
**Status:** Not tested

## Scenario 7: Requirements-informed exploration
**Input:** Step + codebase dir + goal_dir with `refined_requirements.collab.md`
**Expected:** Agent reads requirements BEFORE exploring code. Findings are targeted to the goal's actual needs — not a generic codebase tour. Key Takeaways reference how the code relates to the requirements.
**Status:** Not tested

## Scenario 8: Large codebase scoping
**Input:** Step about a narrow topic + codebase dir with 1000+ files
**Expected:** Agent focuses exploration on areas relevant to the step's question. Notes what was scoped out. Does not attempt to read every file. Completes within timeout.
**Status:** Not tested
