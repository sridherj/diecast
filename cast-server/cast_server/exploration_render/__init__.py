"""The exploration-specific pure layer (exploration-pipeline-nxm sub-phase 4).

Mirrors how `requirements_render/` holds the pure data/gate layer beneath `render_job_service`:
this package holds the exploration corpus loader + source digest (`corpus`) and the exploration
checker verdict (`verdict`), beneath the `exploration_render_service` orchestrator. Exploration-
specific (NOT shared with requirements) — it builds on `render_common`, never the reverse.
"""
