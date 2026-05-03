# `~/.cast/config.yaml` Reference

Diecast stores user-level preferences at `~/.cast/config.yaml`. The file is
created by `./setup` Step 6 on first run; subsequent runs preserve any
user-set values and fill in missing keys with defaults.

The canonical schema below is the one written by `./setup`. Every key listed
here is honored by Diecast — extra keys are tolerated but ignored.

```yaml
# ~/.cast/config.yaml — Diecast user-level config.
# Schema reference: docs/config.md inside the diecast repo.
# Edits here are preserved by ./setup re-runs and /cast-upgrade.
terminal_default: ""
host: localhost
port: 8005
auto_upgrade: false
upgrade_snooze_until: null
upgrade_snooze_streak: 0
upgrade_never_ask: false
last_upgrade_check_at: null
proactive_global: null
proactive_overrides: {}
```

## Keys

### `terminal_default`

- **Default:** `""` (empty string).
- **Valid values:** any non-empty string from the supported terminal list, or
  `""` to fall back to `$TERMINAL` and PATH discovery. The full list of
  recognised names lives in `agents/_shared/terminal.py` and
  `docs/terminals.md` (the latter is owned by sp3).
- **When read:** `cast-spawn-child` reads it via the `$CAST_TERMINAL` env-var
  contract before launching a child agent in a new terminal window.
  `bin/cast-doctor` also surfaces the value during prereq checks.
- **Set by:** `./setup` Step 7 (interactive prompt), `bin/cast-doctor
  --fix-terminal`, or by hand.  An unsupported value soft-falls back to the
  first supported terminal on `PATH` (Decision #3) and prints a warning.
- **Legacy alias:** `terminal` is accepted as a read-time alias for
  back-compatibility. When `./setup` encounters a config with the old
  `terminal` key, it migrates the value to `terminal_default` and removes
  the legacy key. New installs always write `terminal_default`.

### `host`

- **Default:** `localhost`.
- **Valid values:** any hostname or IP literal Diecast clients can resolve.
- **When read:** the *client side* of the wire — skills, agents, and the
  cast-server's own callback URLs in agent prompts. Read by
  `cast-server/cast_server/config.py` as `DEFAULT_CAST_HOST` (env var
  `CAST_HOST` overrides).
- **Asymmetry:** the server-side bind address is **not** in this file. It is
  controlled exclusively by the `CAST_BIND_HOST` env var (default `127.0.0.1`)
  to keep advanced overrides (`0.0.0.0` for LAN exposure, etc.) out of the
  per-user config schema.
- **Set by:** the user, or `./setup` Step 6 on first run.

### `port`

- **Default:** `8005`.
- **Valid values:** integer 1–65535.
- **When read:** both client and server. Read by
  `cast-server/cast_server/config.py` as `DEFAULT_CAST_PORT` (env var
  `CAST_PORT` overrides). The launcher `bin/cast-server` and every
  Diecast-aware skill or agent default to this port.
- **Set by:** the user, or `./setup` Step 6 on first run.

> **Env-var summary**
>
> - `CAST_HOST` — client-side connect target (default `localhost`).
> - `CAST_BIND_HOST` — server-side uvicorn bind (default `127.0.0.1`,
>   env-var-only, intentionally not in `config.yaml`).
> - `CAST_PORT` — shared by both sides (default `8005`).

### `auto_upgrade`

- **Default:** `false`.
- **Valid values:** boolean.
- **When read:** `/cast-upgrade` checks this before prompting; if `true`, it
  skips the AskUserQuestion prompt and proceeds to upgrade immediately.
- **Set by:** the user, or by `/cast-upgrade` when they pick "Always keep me
  up to date" in the upgrade prompt.

### `upgrade_snooze_until`

- **Default:** `null`.
- **Valid values:** ISO-8601 UTC timestamp or `null`.
- **When read:** `/cast-upgrade` exits silently if `now() < upgrade_snooze_until`.
- **Set by:** `/cast-upgrade` when the user picks "Not now"; the value is
  computed from `[24h, 48h, 168h][min(upgrade_snooze_streak, 2)]`.

### `upgrade_snooze_streak`

- **Default:** `0`.
- **Valid values:** non-negative integer.
- **When read:** `/cast-upgrade` uses it to index the snooze backoff schedule
  (24h → 48h → 1 week).
- **Set by:** `/cast-upgrade` increments on every "Not now" choice and resets
  to `0` on a successful upgrade.

### `upgrade_never_ask`

- **Default:** `false`.
- **Valid values:** boolean.
- **When read:** `/cast-upgrade` exits silently when `true`.
- **Set by:** the user, or by `/cast-upgrade` when they pick "Never ask
  again" in the upgrade prompt.

### `last_upgrade_check_at`

- **Default:** `null`.
- **Valid values:** ISO-8601 UTC timestamp or `null`.
- **When read:** `/cast-upgrade` uses it to cache the result of
  `git ls-remote` for one hour (TTL).
- **Set by:** `/cast-upgrade` after each remote check.

### `proactive_global`

- **Default:** `null`.
- **Valid values:** `null`, or one of the proactive defaults the agents
  recognise (typically `"on"` / `"off"`).
- **When read:** every cast-\* agent that supports a proactive default. When
  non-null, this overrides every per-agent default.
- **Set by:** the user, or by helpers under `bin/set-proactive-defaults.py`.

### `proactive_overrides`

- **Default:** `{}` (empty mapping).
- **Valid values:** mapping of `cast-<name>` → boolean (or `null` to inherit).
- **When read:** every cast-\* agent consults its entry before falling back to
  `proactive_global` and then to its own default.
- **Set by:** the user. Example:

  ```yaml
  proactive_overrides:
    cast-refine-requirements: false
    cast-explore: true
  ```

## Authoring guidelines

- Comments are preserved across re-runs only when they sit in the canonical
  header block. Inline comments on individual keys may be rewritten by
  `./setup`.
- Order is preserved best-effort; the merger writes keys in the canonical
  order shown above.
- To reset a key to its default, delete the line and re-run `./setup`. The
  installer fills in any missing key.

## Cross-references

- `./setup --help` points here.
- `bin/cast-doctor` surfaces `$CAST_TERMINAL` issues against this schema.
- `/cast-upgrade` (sp2b) uses every `upgrade_*` key.
