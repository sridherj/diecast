# cast-server

Local FastAPI app that serves the Diecast UI and `/api/agents/*` routes on
`127.0.0.1:8000`.

## Running cast-server

The repo-root launcher `bin/cast-server` is the entry point. It execs
`uvicorn cast_server.app:app` with loopback bind defaults.

```bash
bin/cast-server
```

Phase 4's `./setup` script symlinks `bin/cast-server` into PATH so you can
run it from anywhere.

### Environment variables

| Variable      | Default                | Purpose                                        |
|---------------|------------------------|------------------------------------------------|
| `CAST_HOST`   | `127.0.0.1`            | Bind address. Loopback-only by design.         |
| `CAST_PORT`   | `8000`                 | TCP port.                                      |
| `CAST_DB`     | `~/.cast/diecast.db`   | SQLite path. Parent dir is auto-created.       |

### First-run preflight

If `uvicorn` is not on PATH, `bin/cast-server` exits 1 with a Diecast-branded
message pointing at `./setup`. Install dependencies with `./setup` (preferred)
or `pip install uvicorn`.

### Database location

By default, the SQLite DB lives at `~/.cast/diecast.db`. The directory is
created on first start. Set `CAST_DB=/path/to/file.db` to override; the parent
directory of the override path is also auto-created.

## Tests

```bash
pytest cast-server/tests/                                # unit
pytest cast-server/tests/ -v -m integration              # integration (incl. bind-address)
```

The bind-address regression test (`tests/test_bind_address.py`) spawns the
launcher and asserts loopback-only binding so a `0.0.0.0` debug edit cannot
ship silently.
