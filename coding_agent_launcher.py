#!/usr/bin/env python3
"""Unified Claude Code launcher with project selection and recent directory tracking.

Displays:
- Current directory with Enter to continue
- Numbered/lettered list of projects from projects.yaml
- Numbered/lettered list of recent directories (excluding project dirs)

Options 1-9 use digits, options 10+ use letters (a-z).
All selections are instant (single keypress). Menu actions use Ctrl+key.

Returns selected directory path to stdout for shell integration.
"""

import os
import random
import sys
import tty
import termios
from datetime import datetime
from pathlib import Path

import yaml


PROJECTS_DIR = Path.home() / "Documents" / "github_repos" / "flytival-pjh"
PROJECTS_FILE = PROJECTS_DIR / "projects.yaml"
REPOS_FILE = PROJECTS_DIR / "repositories.yaml"
RECENT_DIRS_FILE = Path.home() / ".cc_recent_dirs"
RECENT_DIRS_DISPLAY_LIMIT = 10
RECENT_DIRS_FILE_LIMIT = 50

# Letters for options 10+ (full alphabet)
OPTION_LETTERS = "abcdefghijklmnopqrstuvwxyz"  # 26 letters for options 10-35

# ANSI escape codes
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
WHITE = "\033[37m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
BRIGHT_CYAN = "\033[96m"
BRIGHT_YELLOW = "\033[93m"
BRIGHT_GREEN = "\033[92m"
BRIGHT_MAGENTA = "\033[95m"
BRIGHT_BLUE = "\033[94m"

USER = "Benedikt"  # Change this to your name for personalized greetings

def _greeting() -> str:
    """Return a random time-appropriate greeting."""
    hour = datetime.now().hour
    day_name = datetime.now().strftime("%A")

    if hour < 12:
        time_greetings = [f"Good morning, {USER}!", f"Morning, {USER}!", f"Good morning, {USER}!"]
    elif hour < 17:
        time_greetings = [f"Good afternoon, {USER}!", f"Afternoon, {USER}!", f"Good afternoon, {USER}!"]
    else:
        time_greetings = [f"Good evening, {USER}!", f"Evening, {USER}!", f"Good evening, {USER}!"]

    generic = [f"Hey {USER}!", f"Hi {USER}!", f"Hello, {USER}!"]
    day_specific = [f"Happy {day_name}!", f"Happy {day_name}, {USER}!"]

    # Weight: 60% time-based, 20% generic, 20% day-specific
    pool = time_greetings * 3 + generic + day_specific
    return random.choice(pool)


def index_to_key(idx: int) -> str:
    """Convert 1-based index to display key (1-9, then a-z)."""
    if 1 <= idx <= 9:
        return str(idx)
    elif 10 <= idx <= 9 + len(OPTION_LETTERS):
        return OPTION_LETTERS[idx - 10]
    else:
        return "?"


def key_to_index(key: str) -> int | None:
    """Convert keypress to 1-based index, or None if invalid."""
    if key.isdigit() and key != "0":
        return int(key)
    elif key.lower() in OPTION_LETTERS:
        return 10 + OPTION_LETTERS.index(key.lower())
    return None


def getch() -> str:
    """Read a single character from stdin without waiting for Enter."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def load_projects() -> list[dict]:
    """Load projects from the index file."""
    if not PROJECTS_FILE.exists():
        return []

    with open(PROJECTS_FILE) as f:
        data = yaml.safe_load(f)

    return data.get("projects", []) if data else []


def load_repositories() -> list[dict]:
    """Load repositories from repositories.yaml."""
    if not REPOS_FILE.exists():
        return []

    with open(REPOS_FILE) as f:
        data = yaml.safe_load(f)

    return data.get("repositories", []) if data else []


def get_project_paths(projects: list[dict]) -> set[str]:
    """Get set of all project directory paths."""
    paths = set()
    for p in projects:
        folder = p.get("folder", "")
        if folder:
            path = PROJECTS_DIR / folder
            paths.add(str(path))
    return paths


def load_recent_dirs(exclude_paths: set[str]) -> list[str]:
    """Load recent directories, excluding project paths, deduplicated, most recent first."""
    if not RECENT_DIRS_FILE.exists():
        return []

    with open(RECENT_DIRS_FILE) as f:
        lines = [line.strip() for line in f if line.strip()]

    # Reverse to get most recent first, deduplicate while preserving order
    seen = set()
    recent = []
    for d in reversed(lines):
        if d not in seen and d not in exclude_paths and Path(d).exists():
            seen.add(d)
            recent.append(d)

    return recent


def trim_recent_dirs_file():
    """Trim the recent dirs file to the limit."""
    if not RECENT_DIRS_FILE.exists():
        return

    with open(RECENT_DIRS_FILE) as f:
        lines = [line.strip() for line in f if line.strip()]

    if len(lines) > RECENT_DIRS_FILE_LIMIT:
        # Keep the most recent entries
        lines = lines[-RECENT_DIRS_FILE_LIMIT:]
        with open(RECENT_DIRS_FILE, 'w') as f:
            f.write('\n'.join(lines) + '\n')


def _print_table(title: str, rows: list[tuple[str, str]], key_colour: str = CYAN, name_colour: str = ""):
    """Print rows as an ASCII table with box-drawing characters."""
    if not rows:
        return
    try:
        term_width = os.get_terminal_size(sys.stderr.fileno()).columns
    except OSError:
        term_width = 80
    key_width = max(len(r[0]) for r in rows)
    key_width = max(key_width, 1)  # minimum 1
    table_chrome = 8 + key_width  # "  │ " + key + " │ " + " │"
    max_name = term_width - table_chrome
    rows = [(k, n[:max_name - 1] + "…" if len(n) > max_name else n) for k, n in rows]
    name_width = max(len(r[1]) for r in rows)
    print(f"\n  {BOLD}{title}:{RESET}", file=sys.stderr)
    print(f"  {DIM}┌─{'─' * key_width}─┬─{'─' * name_width}─┐{RESET}", file=sys.stderr)
    for j, (key, name) in enumerate(rows):
        n_str = f"{name_colour}{name:<{name_width}}{RESET}" if name_colour else f"{name:<{name_width}}"
        print(f"  {DIM}│{RESET} {key_colour}{BOLD}{key:>{key_width}}{RESET} {DIM}│{RESET} {n_str} {DIM}│{RESET}", file=sys.stderr)
        if j < len(rows) - 1:
            print(f"  {DIM}├─{'─' * key_width}─┼─{'─' * name_width}─┤{RESET}", file=sys.stderr)
    print(f"  {DIM}└─{'─' * key_width}─┴─{'─' * name_width}─┘{RESET}", file=sys.stderr)


def _print_dual_table(title: str, left: list[tuple[str, str]], right: list[tuple[str, str]]):
    """Print two sets of rows side by side in a 4-column table."""
    if not left and not right:
        return
    try:
        term_width = os.get_terminal_size(sys.stderr.fileno()).columns
    except OSError:
        term_width = 80

    lk_w = max((len(r[0]) for r in left), default=1)
    rk_w = max((len(r[0]) for r in right), default=1)
    # Chrome: "  │ " + lk + " │ " + lname + " │ " + rk + " │ " + rname + " │"
    chrome = 16 + lk_w + rk_w
    avail = term_width - chrome
    ln_w = max((len(r[1]) for r in left), default=0)
    rn_w = max((len(r[1]) for r in right), default=0)
    # Cap names to fit terminal
    if ln_w + rn_w > avail:
        half = avail // 2
        ln_w = min(ln_w, half)
        rn_w = min(rn_w, avail - ln_w)
    else:
        ln_w = max(ln_w, 1)
        rn_w = max(rn_w, 1)

    # Truncate names
    left = [(k, n[:ln_w - 1] + "…" if len(n) > ln_w else n) for k, n in left]
    right = [(k, n[:rn_w - 1] + "…" if len(n) > rn_w else n) for k, n in right]

    num_rows = max(len(left), len(right))
    print(f"\n  {BOLD}{title}:{RESET}", file=sys.stderr)
    print(f"  {DIM}┌─{'─' * lk_w}─┬─{'─' * ln_w}─┬─{'─' * rk_w}─┬─{'─' * rn_w}─┐{RESET}", file=sys.stderr)
    for j in range(num_rows):
        lk = left[j][0] if j < len(left) else ""
        ln = left[j][1] if j < len(left) else ""
        rk = right[j][0] if j < len(right) else ""
        rn = right[j][1] if j < len(right) else ""
        lk_styled = f"{CYAN}{BOLD}{lk:>{lk_w}}{RESET}" if lk else f"{lk:>{lk_w}}"
        rk_styled = f"{YELLOW}{BOLD}{rk:>{rk_w}}{RESET}" if rk else f"{rk:>{rk_w}}"
        print(f"  {DIM}│{RESET} {lk_styled} {DIM}│{RESET} {ln:<{ln_w}} {DIM}│{RESET} {rk_styled} {DIM}│{RESET} {rn:<{rn_w}} {DIM}│{RESET}", file=sys.stderr)
        if j < num_rows - 1:
            print(f"  {DIM}├─{'─' * lk_w}─┼─{'─' * ln_w}─┼─{'─' * rk_w}─┼─{'─' * rn_w}─┤{RESET}", file=sys.stderr)
    print(f"  {DIM}└─{'─' * lk_w}─┴─{'─' * ln_w}─┴─{'─' * rk_w}─┴─{'─' * rn_w}─┘{RESET}", file=sys.stderr)


def display_menu(
    current_dir: str,
    projects: list[dict],
    repositories: list[dict],
    recent_dirs: list[str],
    show_archived: bool = False,
    show_all_recent: bool = False,
    total_recent: int = 0
) -> tuple[list[dict], list[str]]:
    """Display the menu and return (displayed_projects, displayed_recent_dirs)."""
    # Clear screen and move cursor to top
    print("\033[2J\033[H", file=sys.stderr, end="")

    # Greeting
    print(f"  {BRIGHT_MAGENTA}{BOLD}{_greeting()}{RESET}", file=sys.stderr)

    # Filter projects
    if show_archived:
        displayed_projects = projects  # Preserve YAML order
    else:
        displayed_projects = [p for p in projects if p.get("status") == "active"]

    # Build project rows
    project_rows = []
    for i, p in enumerate(displayed_projects, 1):
        key = index_to_key(i)
        name = p.get("name", p.get("folder", "Unnamed"))
        if show_archived and p.get("status") != "active":
            name = f"{name} ({p.get('status', '')})"
        project_rows.append((key, name))

    # Build repository rows (r + 1, r + 2, etc.)
    repo_rows = []
    for i, r in enumerate(repositories, 1):
        key = f"r{i}"
        name = Path(r.get("path", "")).name
        repo_rows.append((key, name))

    # Build recent rows
    if show_all_recent:
        displayed_recent = recent_dirs
    else:
        displayed_recent = recent_dirs[:RECENT_DIRS_DISPLAY_LIMIT]

    recent_rows = []
    start_idx = len(displayed_projects) + 1
    for i, d in enumerate(displayed_recent):
        key = index_to_key(start_idx + i)
        p = Path(d)
        short = f"{p.parent.name}/{p.name}"
        recent_rows.append((key, short))

    # Print projects and repos as a combined table
    if repo_rows:
        _print_dual_table("Projects & repos", project_rows, repo_rows)
    else:
        _print_table("Projects", project_rows)

    if recent_rows:
        _print_table("Recent", recent_rows)
        if not show_all_recent and total_recent > RECENT_DIRS_DISPLAY_LIMIT:
            print(f"  {DIM}... ({total_recent - RECENT_DIRS_DISPLAY_LIMIT} more){RESET}", file=sys.stderr)

    if not recent_dirs:
        displayed_recent = []

    # Footer
    print(file=sys.stderr)
    archived_count = len([p for p in projects if p.get("status") != "active"])

    hints = []
    if not show_all_recent and total_recent > RECENT_DIRS_DISPLAY_LIMIT:
        hints.append("^A all recent")
    if not show_archived and archived_count > 0:
        hints.append(f"^Z archived (+{archived_count})")
    hints.append("^C quit")

    print(f"  {DIM}{'  '.join(hints)}{RESET}", file=sys.stderr)
    print(file=sys.stderr)
    print(f"  {BOLD}Current:{RESET} {GREEN}{current_dir}{RESET} {DIM}⏎{RESET}", file=sys.stderr)
    print(file=sys.stderr)

    return displayed_projects, displayed_recent


def select_option(idx: int, displayed_projects: list[dict], displayed_recent: list[str]) -> bool:
    """Try to select option by index. Returns True if successful (exits), False otherwise."""
    total_options = len(displayed_projects) + len(displayed_recent)

    if not (1 <= idx <= total_options):
        return False

    if idx <= len(displayed_projects):
        # Project selection
        folder = displayed_projects[idx - 1].get("folder", "")
        name = displayed_projects[idx - 1].get("name", folder)
        path = PROJECTS_DIR / folder
        if path.exists():
            print(f"\n  Opening {name}...\n", file=sys.stderr)
            print(path)
            sys.exit(0)
        else:
            print(f"Directory not found: {path}", file=sys.stderr)
            return False
    else:
        # Recent dir selection
        recent_idx = idx - len(displayed_projects) - 1
        if recent_idx < len(displayed_recent):
            path = displayed_recent[recent_idx]
            print(f"\n  Opening {path}...\n", file=sys.stderr)
            print(path)
            sys.exit(0)

    return False


def add_project(name: str, folder: str):
    """Append a new active project entry to projects.yaml."""
    if not PROJECTS_FILE.exists():
        print(f"projects.yaml not found: {PROJECTS_FILE}", file=sys.stderr)
        sys.exit(1)

    projects = load_projects()
    for p in projects:
        if p.get("name") == name:
            print(f"Project '{name}' already exists.", file=sys.stderr)
            sys.exit(1)
        if p.get("folder") == folder:
            print(f"Folder already registered as '{p.get('name')}'.", file=sys.stderr)
            sys.exit(1)

    folder_path = Path(folder).expanduser()
    if not folder_path.exists():
        folder_path.mkdir(parents=True)
        print(f"Created directory: {folder_path}", file=sys.stderr)

    entry = f'\n  - name: "{name}"\n    folder: "{folder_path}"\n    status: active\n'
    with open(PROJECTS_FILE, "a") as f:
        f.write(entry)

    print(f"Added project '{name}' → {folder_path}", file=sys.stderr)


def add_repo(name: str, path: str):
    """Append a new repository entry to repositories.yaml."""
    if not REPOS_FILE.exists():
        print(f"repositories.yaml not found: {REPOS_FILE}", file=sys.stderr)
        sys.exit(1)

    repos = load_repositories()
    for r in repos:
        if r.get("name") == name:
            print(f"Repository '{name}' already exists.", file=sys.stderr)
            sys.exit(1)
        if r.get("path") == path:
            print(f"Path already registered as '{r.get('name')}'.", file=sys.stderr)
            sys.exit(1)

    repo_path = Path(path).expanduser()
    if not repo_path.exists():
        repo_path.mkdir(parents=True)
        print(f"Created directory: {repo_path}", file=sys.stderr)

    entry = f'\n  - path: "{repo_path}"\n    name: "{name}"\n'
    with open(REPOS_FILE, "a") as f:
        f.write(entry)

    print(f"Added repository '{name}' → {repo_path}", file=sys.stderr)


def prompt_folder(current_dir: str) -> str:
    """Ask the user how to set the folder for a new project."""
    print(f"\n  Set project folder:", file=sys.stderr)
    print(f"  {CYAN}{BOLD}1{RESET}  Use current directory  {DIM}({current_dir}){RESET}", file=sys.stderr)
    print(f"  {CYAN}{BOLD}2{RESET}  Enter path manually", file=sys.stderr)
    print(file=sys.stderr)

    while True:
        ch = getch()
        if ch == '1':
            print(file=sys.stderr)
            return current_dir
        elif ch == '2':
            # Restore normal terminal input for typing
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                print(f"  Path: ", file=sys.stderr, end="", flush=True)
                path = input()
            finally:
                pass
            return path.strip()
        elif ch in ('\x03', '\x04'):
            print(file=sys.stderr)
            sys.exit(1)


def main():
    args = sys.argv[1:]
    select_key = None
    current_dir = os.getcwd()
    i = 0
    while i < len(args):
        if args[i] == '--select' and i + 1 < len(args):
            select_key = args[i + 1]
            i += 2
        else:
            current_dir = args[i]
            i += 1

    # np / nr subcommands — last positional arg is always $PWD from the shell function
    if args and args[0] == 'np':
        if len(args) < 2:
            print("Usage: cc np PROJECT_NAME", file=sys.stderr)
            sys.exit(1)
        name = args[1]
        folder = prompt_folder(current_dir)
        add_project(name, folder)
        sys.exit(0)

    if args and args[0] == 'nr':
        if len(args) < 2:
            print("Usage: cc nr REPO_NAME", file=sys.stderr)
            sys.exit(1)
        name = args[1]
        path = prompt_folder(current_dir)
        add_repo(name, path)
        sys.exit(0)

    if select_key is not None:
        projects = load_projects()
        active = [p for p in projects if p.get('status') == 'active']
        repositories = load_repositories()
        project_paths = get_project_paths(projects)
        repo_paths = {r.get("path", "") for r in repositories}
        recent_dirs = load_recent_dirs(project_paths | repo_paths)

        # Repository selection: r1, r2, etc.
        if select_key.startswith('r') and select_key[1:].isdigit():
            repo_idx = int(select_key[1:]) - 1
            if 0 <= repo_idx < len(repositories):
                path = repositories[repo_idx].get("path", "")
                name = repositories[repo_idx].get("name", Path(path).name)
                if Path(path).exists():
                    print(f"\n  Opening {name}...\n", file=sys.stderr)
                    print(path)
                    sys.exit(0)
            print(f"No repo {select_key}", file=sys.stderr)
            sys.exit(1)

        # Convert key to index (works for digits 1-9 and letters a-z)
        idx = key_to_index(select_key)
        if idx is not None:
            if 1 <= idx <= len(active):
                folder = active[idx - 1].get('folder', '')
                name = active[idx - 1].get('name', folder)
                path = PROJECTS_DIR / folder
                if path.exists():
                    print(f"\n  Opening {name}...\n", file=sys.stderr)
                    print(path)
                    sys.exit(0)
            else:
                recent_idx = idx - len(active) - 1
                if 0 <= recent_idx < len(recent_dirs):
                    path = recent_dirs[recent_idx]
                    short = f"{Path(path).parent.name}/{Path(path).name}"
                    print(f"\n  Opening {short}...\n", file=sys.stderr)
                    print(path)
                    sys.exit(0)

        print(f"No option '{select_key}'", file=sys.stderr)
        sys.exit(1)

    # Trim recent dirs file periodically
    trim_recent_dirs_file()

    # Load data
    projects = load_projects()
    repositories = load_repositories()
    project_paths = get_project_paths(projects)
    # Also exclude repository paths from recent dirs
    repo_paths = {r.get("path", "") for r in repositories}
    all_recent_dirs = load_recent_dirs(project_paths | repo_paths)
    total_recent = len(all_recent_dirs)

    show_archived = False
    show_all_recent = False

    displayed_projects, displayed_recent = display_menu(
        current_dir, projects, repositories, all_recent_dirs, show_archived, show_all_recent, total_recent
    )

    while True:
        try:
            ch = getch()
        except (EOFError, KeyboardInterrupt):
            print(file=sys.stderr)
            sys.exit(1)

        # Handle Ctrl+C, Ctrl+D, Ctrl+Q - quit
        if ch in ('\x03', '\x04', '\x11'):
            print(file=sys.stderr)
            sys.exit(1)

        # Enter - use current directory
        if ch in ('\n', '\r'):
            print(f"\n  Using current directory...\n", file=sys.stderr)
            print(current_dir)
            sys.exit(0)

        # 'r' prefix - select repository (wait for digit)
        if ch == 'r' and repositories:
            ch2 = getch()
            if ch2.isdigit() and ch2 != '0':
                repo_idx = int(ch2) - 1
                if 0 <= repo_idx < len(repositories):
                    path = repositories[repo_idx].get("path", "")
                    name = repositories[repo_idx].get("name", Path(path).name)
                    if Path(path).exists():
                        print(f"\n  Opening {name}...\n", file=sys.stderr)
                        print(path)
                        sys.exit(0)
                    else:
                        print(f"Directory not found: {path}", file=sys.stderr)
            continue

        # Ctrl+A - show all recent
        if ch == '\x01' and not show_all_recent and total_recent > RECENT_DIRS_DISPLAY_LIMIT:
            show_all_recent = True
            displayed_projects, displayed_recent = display_menu(
                current_dir, projects, repositories, all_recent_dirs, show_archived, show_all_recent, total_recent
            )
            continue

        # Ctrl+Z - show archived
        if ch == '\x1a' and not show_archived:
            show_archived = True
            displayed_projects, displayed_recent = display_menu(
                current_dir, projects, repositories, all_recent_dirs, show_archived, show_all_recent, total_recent
            )
            continue

        # Try to select by key (digit 1-9 or letter a-z)
        if len(ch) == 1:
            idx = key_to_index(ch)
            if idx is not None:
                select_option(idx, displayed_projects, displayed_recent)
                # If select_option returns (didn't exit), the selection failed - just continue


if __name__ == "__main__":
    main()