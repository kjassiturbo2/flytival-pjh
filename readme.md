# Claude Code / Codex Project Switcher

A terminal project launcher for [Claude Code](https://claude.ai/code) and Codex. Press `cc` to jump into any project and launch your coding agent in the right directory.

Based on [Peter Hartree's guide](https://wow.pjh.is/journal/claude-code-project-switcher).

---

## How it works

Run `cc` from your shell. It displays an interactive menu of your projects, pinned repositories, and recently visited directories. Press a key to select — the script outputs the chosen path so a shell function can `cd` into it and launch Claude Code (or Codex).

Menu output goes to `stderr`; the selected path goes to `stdout` — that's what makes shell integration clean.

---

## Requirements

- Python 3.10+
- PyYAML

```bash
pip install pyyaml
```

---

## Setup

### 1. Place the files

Clone or copy this repo to wherever you'd like to keep it, e.g.:

```
~/your/chosen/path/
├── coding_agent_launcher.py
├── projects.yaml
└── repositories.yaml
```

Then open `coding_agent_launcher.py` and update the path constants near the top to match your chosen location:

```python
PROJECTS_DIR = Path.home() / "your" / "chosen" / "path"
```

### 2. Add shell functions

Add this to your `~/.zshrc` or `~/.bashrc`, replacing the path with wherever you placed the files:

```bash
function cc() {
  if [[ "$1" == "np" || "$1" == "nr" ]]; then
    python3 ~/your/chosen/path/coding_agent_launcher.py "$1" "${@:2}" "$PWD"
    return
  fi
  local dir
  dir=$(python3 ~/your/chosen/path/coding_agent_launcher.py "$PWD")
  if [ $? -eq 0 ] && [ -n "$dir" ]; then
    cd "$dir" && claude
  fi
}

function cx() {
  if [[ "$1" == "np" || "$1" == "nr" ]]; then
    python3 ~/your/chosen/path/coding_agent_launcher.py "$1" "${@:2}" "$PWD"
    return
  fi
  local dir
  dir=$(python3 ~/your/chosen/path/coding_agent_launcher.py "$PWD")
  if [ $? -eq 0 ] && [ -n "$dir" ]; then
    cd "$dir" && codex
  fi
}
```

`cc` launches Claude Code after switching directories; `cx` launches Codex. Both support the `np` and `nr` subcommands.

### 3. Track recent directories (optional)

To populate the **Recent** section, use a `chpwd` hook (zsh) to track every directory change:

```bash
chpwd() { echo "$PWD" >> ~/.cc_recent_dirs }
```

---

## projects.yaml

Lists your projects. Only `active` projects appear by default; archived ones are hidden unless you press `Ctrl+Z`.

```yaml
projects:
  - name: "My Project"
    folder: "/Users/you/path/to/my-project"
    status: active

  - name: "Old Project"
    folder: "/Users/you/path/to/old-project"
    status: archived
```

Fields:

| Field    | Description                              |
|----------|------------------------------------------|
| `name`   | Display name shown in the menu           |
| `folder` | Absolute path to the project directory   |
| `status` | `active` (shown) or `archived` (hidden)  |

---

## repositories.yaml

A separate list of pinned repositories accessible with `r` + a digit (e.g. `r1`, `r2`). Useful for repos you want instant access to regardless of project status.

```yaml
repositories:
  - path: "/Users/you/path/to/my-repo"
    name: "my-repo"

  - path: "/Users/you/path/to/another-repo"
    name: "another-repo"
```

Fields:

| Field  | Description                            |
|--------|----------------------------------------|
| `path` | Absolute path to the repository        |
| `name` | Display name shown in the menu         |

---

## Usage

Run `cc` from your terminal. The menu looks like this:

```
  Good morning!

  Projects & repos:
  ┌───┬─────────────────────┬────┬──────────────────┐
  │ 1 │ My Project          │ r1 │ my-repo          │
  ├───┼─────────────────────┼────┼──────────────────┤
  │ 2 │ Another Project     │ r2 │ another-repo     │
  └───┴─────────────────────┴────┴──────────────────┘

  Recent:
  ┌───┬──────────────────────┐
  │ a │ projects/some-dir    │
  └───┴──────────────────────┘

  ^Z archived (+1)  ^C quit

  Current: /Users/you  ⏎
```

### Keybindings

| Key          | Action                                      |
|--------------|---------------------------------------------|
| `1`–`9`      | Select project by number                    |
| `a`–`z`      | Select project or recent dir (options 10+)  |
| `r1`–`r9`    | Select pinned repository                    |
| `Enter`      | Use current directory (no switch)           |
| `Ctrl+Z`     | Show archived projects                      |
| `Ctrl+A`     | Show all recent directories                 |
| `Ctrl+C`     | Quit                                        |

### Adding projects and repositories

```bash
cc np "My New Project"   # add a new project entry to projects.yaml
cc nr "my-new-repo"      # add a new repository entry to repositories.yaml
```

`cx np` and `cx nr` work identically — both `cc` and `cx` share the same subcommands.

Both commands prompt you to either use the current directory or enter a path manually.

### Direct selection (optional)

You can also call the script with `--select` to skip the interactive menu:

```bash
python3 ~/your/chosen/path/coding_agent_launcher.py --select 1
python3 ~/your/chosen/path/coding_agent_launcher.py --select r2
```

This is useful for scripting or keybinding shortcuts outside the menu.
