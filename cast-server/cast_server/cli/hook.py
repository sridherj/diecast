"""cast-hook CLI. Console_script registered in pyproject.toml.

Subcommands:
  user-prompt-start   (UserPromptSubmit hook)
  user-prompt-stop    (Stop hook)
  subagent-start      (SubagentStart hook)
  subagent-stop       (SubagentStop hook)
  skill-invoke        (PreToolUse hook with matcher: "Skill")
  install [--user]    (write entries to .claude/settings.json)
  uninstall [--user]  (remove our entries; preserve everything else)
"""
import sys
from pathlib import Path

from cast_server.cli import install_hooks
from cast_server.cli.hook_events import DISPATCH


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(
            "Usage: cast-hook {user-prompt-start | user-prompt-stop | "
            "subagent-start | subagent-stop | skill-invoke | install | uninstall} [args]",
            file=sys.stderr,
        )
        return 0
    sub = argv[0]
    if sub in DISPATCH:
        DISPATCH[sub]()
        return 0  # never block the user
    if sub in ("install", "uninstall"):
        user_scope = "--user" in argv
        project_root = Path.cwd()
        fn = install_hooks.install if sub == "install" else install_hooks.uninstall
        return fn(project_root=project_root, user_scope=user_scope)
    print(f"Unknown subcommand: {sub}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
