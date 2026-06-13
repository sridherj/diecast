# Bug Fix Missing Evidence (MUST FAIL under --family bug_fix)

## Intent

The refine endpoint returns a 500 when the writeup has no front matter; it
should fall back to an empty header instead of raising.
