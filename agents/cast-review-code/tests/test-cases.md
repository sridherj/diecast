# Test Cases: cast-review-code

## TC1: Default mode (git diff)

**Setup:** Have uncommitted changes in 2-3 files.
**Invoke:** `/cast-review-code`
**Expected:**
- Agent detects changed files via `git diff`
- Review brief lists all changed files
- Terminal tab opens with claude review session
- Brief file exists at `/tmp/review-brief-*.md`

## TC2: Specific file paths

**Setup:** Any state.
**Invoke:** `/cast-review-code src/foo.py src/bar.py`
**Expected:**
- Agent uses only the provided file paths
- Review brief lists exactly `src/foo.py` and `src/bar.py`
- No git diff is run

## TC3: No changes found

**Setup:** Clean working tree, no staged changes.
**Invoke:** `/cast-review-code`
**Expected:**
- Agent detects no files from git diff
- Agent asks user what files to review
- Does NOT launch an empty review session

## TC4: Spec matching

**Setup:** Modify a file that appears in a spec's `linked_files` frontmatter.
**Invoke:** `/cast-review-code`
**Expected:**
- Review brief's "Relevant Specs" section lists the matching spec
- At most 2 specs are included
- Spec scope is noted but full behaviors are NOT pasted
