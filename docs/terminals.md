# Supported Terminals

`cast-spawn-child` dispatches a new terminal window for parent-child agent
runs. Set `$CAST_TERMINAL` (or `~/.cast/config.yaml::terminal`) to your
preferred terminal. If unset, the resolver falls back to `$TERMINAL`, then
to the first supported terminal on `PATH` in the order listed below.

## Supported terminals

| Terminal       | `$CAST_TERMINAL` value | How `cast-spawn-child` invokes it                            |
|----------------|------------------------|--------------------------------------------------------------|
| Ptyxis         | `ptyxis`               | `ptyxis --new-window -- bash -c '<cmd>'`                     |
| GNOME Terminal | `gnome-terminal`       | `gnome-terminal --window -- bash -c '<cmd>'`                 |
| kitty          | `kitty`                | `kitty bash -c '<cmd>'`                                      |
| Alacritty      | `alacritty`            | `alacritty -e bash -c '<cmd>'`                               |
| WezTerm        | `wezterm`              | `wezterm start -- bash -c '<cmd>'`                           |
| iTerm2 (macOS) | `iterm2`               | `osascript -e 'tell application "iTerm2" to create window…'` |

The preference order top-to-bottom matches the soft-fallback order used by
`agents/_shared/terminal.py::resolve_terminal()` and surfaced by
`bin/cast-doctor`.

## Unsupported terminal values

If `$CAST_TERMINAL` is set to a value not in the table above (e.g. `warp`,
`tabby`, `hyper`), `cast-spawn-child` falls back to the first supported
terminal on `PATH` (preference order matches the table top-to-bottom) and
prints:

```
Warning: $CAST_TERMINAL=<value> not supported; falling back to <picked>.
See docs/terminals.md to add support.
```

`bin/cast-doctor` surfaces the same condition during diagnostics with the
same pointer back to this page (Decision #3).

## When no supported terminal is on `PATH`

Both `cast-spawn-child` and `bin/cast-doctor` print a YELLOW warning
listing the supported names. Recovery options:

1. Install one of the supported terminals from your package manager.
2. Set `$CAST_TERMINAL` (or `~/.cast/config.yaml::terminal`) to a value in
   the table above and ensure that binary is on `PATH`.
3. Open a PR adding support for your terminal — see the next section.

## Adding support for a new terminal

1. Open `agents/_shared/terminal.py`.
2. Add an entry to the `SUPPORTED_TERMINALS` registry:
   - the `$CAST_TERMINAL` value users will set,
   - the launcher recipe (a function that returns the `argv` list to
     execute given a child command string),
   - whether the terminal supports a `--new-window` semantic.
3. Add a row to the table above.
4. Add a row to `bin/cast-doctor`'s `SUPPORTED_TERMINALS` array.
5. Add a smoke test under `tests/test_b6_terminal_resolution.py` covering
   the new entry.

PRs welcome. Diecast does not gate on host-OS test coverage — a
manually-verified launcher recipe is enough to ship.

## Why this list

The list is deliberately short and based on what the maintainers and the
early dogfood cohort actually use. Adding more terminals is cheap (the
launcher recipe is the entire integration), but the v1 surface only ships
what is exercised by tests.

## Cross-references

- [`docs/troubleshooting.md`](troubleshooting.md) — recovery recipes for
  the unsupported-terminal warning.
- [`docs/config.md`](config.md) — `~/.cast/config.yaml::terminal` schema.
- [`agents/_shared/terminal.py`](../agents/_shared/terminal.py) —
  `resolve_terminal()` implementation and `SUPPORTED_TERMINALS` registry.
