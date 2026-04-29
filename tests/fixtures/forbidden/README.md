# Anonymization fixtures (`forbidden/`)

Each file in this directory **intentionally contains** a string the
anonymization lint must catch. The directory is excluded from the default
`bin/lint-anonymization` scan; pass `--include-fixtures` to include it.

These files are pattern-coverage canaries. They should not be edited to
remove forbidden content — that is precisely what makes them useful.

If you add a new forbidden pattern in `bin/lint-anonymization`, drop a
companion fixture file here so the manual `--include-fixtures` sweep
keeps full coverage.
