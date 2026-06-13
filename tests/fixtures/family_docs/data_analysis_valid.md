# Data Analysis Fixture

## Intent

Which work families are most common across the existing goal corpus, and how
often does the classifier fall back to `random_idea`?

## Evidence

- Source: `goals/*/refined_requirements.collab.md` front matter.
- 142 goals carry a `classification` block as of 2026-06-11.
- Pull the `family` and `confirmed_by` keys and tabulate by month.
