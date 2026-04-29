# web-researcher

Deep internet research on any topic from 7 expert angles using parallel subagents.

## Type

Claude Code Skill

## I/O Contract

- **Input:** A topic to research, optionally with goal context and output directory
- **Output:** Structured research notes with 7 sections (one per angle) plus consolidated source list

## How It Works

1. Frames the research question
2. Spawns 7 parallel subagents, each searching from a distinct angle:
   - Expert Practitioner (how the best people do it)
   - Tool/Product Landscape (best tools and platforms)
   - AI-Native/Innovation (what AI makes newly possible)
   - Community Wisdom (Reddit, HN, forums)
   - Framework/Methodology (structured approaches)
   - Contrarian (what everyone gets wrong)
   - First Principles (from-scratch rethinking)
3. Each subagent uses WebSearch + WebFetch for real research
4. Assembles all findings into a single structured document

## Usage

```
"research this topic: building developer tools"
"find information about: AI-powered code review"
"deep dive research on: SaaS pricing strategies"
```

## Key Files

- `SKILL.md` — Agent instructions with full subagent prompt templates
