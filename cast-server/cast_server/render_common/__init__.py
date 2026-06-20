"""Shared render-job core (refine-requirements-v3 / exploration-pipeline-nxm sub-phase 4).

The genuinely-shared base that BOTH the requirements render-job (`render_job_service`) and the
exploration render-job (`exploration_render_service`) build on:

- `atomic`           — the atomic file write primitive (`_atomic_write`).
- `agent_runner`     — the tool-free `claude -p` subprocess seam (Protocol + production impl).
- `sentinel`         — the `<!-- BEGIN/END RENDER -->` extraction contract.
- `verdict`          — the generic checker-verdict schema base (coercers, score math, derive_pass).
- `job_runtime`      — the single-flight registry / in-flight semaphore / lazy reaper / row I/O.
- `quality_loop`     — the named-stage quality loop skeleton + terminal `decide_quality`.

HARD RULE: nothing here imports `render_job_service`, `exploration_render_service`, or any
requirements-specific module (block_diff, families, parsed, maker_gate). This is the shared base —
the dependency arrow only ever points INTO this package, never out of it.
"""
