# Shared shell, pluggable renderers

**Outcome:** Reader can describe the two-layer architecture in one sentence.

The review tool has exactly two layers:

- A shared HTML shell (sidebar, header, autosave, export)
- A small set of renderers that each take source files and return slides

Each renderer is a plain Python module that calls `register_renderer(...)`.
No framework, no inheritance, no plugin loader. Dropping a new stage in
means adding a new file under `renderers/` and one line of import.
