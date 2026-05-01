# Diecast roadmap

> **Note on dates:** all targets below are "target ~N days post-launch,"
> not "ships in N days." Diecast is a one-maintainer project; dates slip
> when reality demands.

The roadmap is structured as three milestones — v1.1, v1.2, v2.0 — plus
an explicit kill criterion at +90 days. The kill criterion is a forcing
function. Public failure conditions are disclosed up front so v1.1 is
not a sunk-cost continuation.

## v1.1 — Agent contracts (target ~30 days)

The hardening release. v1.0.0 shipped contract_version `2`; v1.1
solidifies it.

- **Tighter `next_steps` typing.** v1.0 documents `next_steps` as a list
  of strings. v1.1 introduces an optional structured shape (command +
  rationale) while keeping bare strings backward-compatible.
- **`contract_version` v2 hardening.** Closes the validation gaps
  surfaced during the launch window (malformed-output retries,
  string-vs-object drift, ISO-8601 strictness).
- **Opt-in install telemetry.** A single anonymous ping at `./setup`
  time recording version + harness + OS, opt-in via a config flag.
  Goal: count active installs against the kill criterion below
  without scraping GitHub stars.
- **GitHub Discussions volume review.** If launch surfaces real-time
  chat demand, v1.1 reconsiders the v1 "skip Discord" decision and
  ships a Discord conditional on demand. If Discussions is quiet,
  v1.1 doubles down on async.
- **Bug fixes from the launch window.** Whatever the first 30 days
  surfaces.

## v1.2 — Evals harness (target ~60 days)

The discipline release. v1.0 ships paired makers + checkers; v1.2
adds a structured surface for measuring how well the discipline
holds.

- **`cast-evals` agent.** Runs a known input through a maker, runs
  the corresponding checker, records pass/fail + drift metrics.
- **Reference benchmark suite.** Eight to twelve canonical
  cast-crud scenarios with locked-in expected outputs.
- **Drift detection.** Per-checker score over time so contributors
  can see when an agent tweak regresses prior runs.
- **Per-agent benchmark hooks.** New cast-* agents land with a
  benchmark fixture as a contribution requirement.
- **Public results dashboard.** Static HTML in
  `docs/evals/index.html`, regenerated on push.

## v2.0 — PM-tool adapters, starting with Linear (target ~90–120 days)

The integration release. v1.x lives in markdown files on disk; v2
opens a controlled bridge to where work actually gets tracked.

- **Linear adapter first.** A `cast-linear-adapter` agent that maps
  goals → projects, sub-phases → issues, run states → issue
  statuses. Linear chosen because the API is the cleanest.
- **GitHub Issues adapter.** Same shape, different backend.
- **Jira adapter.** Conditional on a Jira-using contributor stepping
  up; the maintainer is not running Jira.
- **Multi-harness consideration.** v2 is the natural place to land
  the [multi-harness](./multi-harness.md) work IF the demand
  conditions on that page are met.

## 90-day kill criterion

> **If at +90 days post-launch:**
>
> - Repo has fewer than 100 stars,
> - Fewer than 15 active users (defined as: at least one `/cast-init`
>   run logged per week in their environment),
> - No third-party agent or skill submissions,
>
> then the public artifact is archived.

This is a forcing function — public failure-condition disclosed up
front so v1.1 isn't a sunk-cost continuation. The maintainer ships
the open-source artifact because the underlying pattern seems to
generalize. If after 90 days no real signal supports that
generalization, archiving is more honest than dragging a v1.1 over
the finish line on willpower.

The kill criterion is not "the project is sad and stopping." It is:
the hypothesis was that the workflow runtime helps people other
than the maintainer. If that hypothesis fails to gather evidence in
90 days, the project is wrong about its own value, and the right
move is to fold it back into private use rather than keep painting
fences.

The metrics above are deliberately moderate. 100 stars in 90 days is
achievable for a real OSS project; 15 active users is the smallest
group that proves "non-author repos run this." Third-party
contributions are the strongest signal that someone other than the
maintainer is invested.

## Out of roadmap (deliberately not promised)

- **A web-based goal manager.** cast-server already ships a local
  web UI; a hosted version is not on the path. State stays on the
  user's disk.
- **A model-agnostic agent runtime.** Diecast lives on top of agent
  harnesses; it does not replace them. If someone wants to run
  cast-* against a fine-tuned local model, the harness is where
  that work belongs, not the chain.
- **Aggregate analytics across users.** Even with v1.1 install
  telemetry, the project does not aggregate per-user behavior. The
  ping is a heartbeat, not a tracker.
